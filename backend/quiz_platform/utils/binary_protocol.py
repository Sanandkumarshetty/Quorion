import logging
import socket
import struct


_FRAME_MAGIC = b"QTP1"
_HEADER_STRUCT = struct.Struct("!4sI")
_INT64_STRUCT = struct.Struct("!q")
_FLOAT64_STRUCT = struct.Struct("!d")
_UINT32_STRUCT = struct.Struct("!I")

_TYPE_NONE = 0x00
_TYPE_FALSE = 0x01
_TYPE_TRUE = 0x02
_TYPE_INT = 0x03
_TYPE_FLOAT = 0x04
_TYPE_STRING = 0x05
_TYPE_BYTES = 0x06
_TYPE_LIST = 0x07
_TYPE_DICT = 0x08


_LOGGER = logging.getLogger("quiz_platform.tcp")
if not _LOGGER.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("[TCP] %(message)s"))
    _LOGGER.addHandler(_handler)
_LOGGER.setLevel(logging.INFO)
_LOGGER.propagate = False


def _socket_name(name_getter):
    try:
        return f"{name_getter()[0]}:{name_getter()[1]}"
    except OSError:
        return "unknown"


def _describe_socket(client_socket):
    local_address = _socket_name(client_socket.getsockname)
    peer_address = _socket_name(client_socket.getpeername)
    return local_address, peer_address


def _log_send(client_socket, message, payload_size, total_size, chunk_sizes):
    local_address, peer_address = _describe_socket(client_socket)
    _LOGGER.info(
        "SEND local=%s peer=%s type=%s action=%s frame_bytes=%s payload_bytes=%s send_calls=%s chunk_sizes=%s",
        local_address,
        peer_address,
        message.get("type"),
        message.get("action"),
        total_size,
        payload_size,
        len(chunk_sizes),
        chunk_sizes,
    )


def _log_receive(client_socket, message, payload_size, header_chunk_sizes, payload_chunk_sizes):
    local_address, peer_address = _describe_socket(client_socket)
    all_chunk_sizes = list(header_chunk_sizes) + list(payload_chunk_sizes)
    _LOGGER.info(
        "RECV local=%s peer=%s type=%s action=%s frame_bytes=%s payload_bytes=%s recv_calls=%s header_calls=%s payload_calls=%s chunk_sizes=%s",
        local_address,
        peer_address,
        message.get("type"),
        message.get("action"),
        _HEADER_STRUCT.size + payload_size,
        payload_size,
        len(all_chunk_sizes),
        len(header_chunk_sizes),
        len(payload_chunk_sizes),
        all_chunk_sizes,
    )


def _pack_uint32(value):
    if value < 0:
        raise ValueError("length-cannot-be-negative")
    return _UINT32_STRUCT.pack(value)


def _encode_value(value):
    if value is None:
        return bytes((_TYPE_NONE,))
    if value is False:
        return bytes((_TYPE_FALSE,))
    if value is True:
        return bytes((_TYPE_TRUE,))
    if isinstance(value, int):
        return bytes((_TYPE_INT,)) + _INT64_STRUCT.pack(value)
    if isinstance(value, float):
        return bytes((_TYPE_FLOAT,)) + _FLOAT64_STRUCT.pack(value)
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return bytes((_TYPE_STRING,)) + _pack_uint32(len(encoded)) + encoded
    if isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
        return bytes((_TYPE_BYTES,)) + _pack_uint32(len(raw)) + raw
    if isinstance(value, (list, tuple)):
        parts = [bytes((_TYPE_LIST,)), _pack_uint32(len(value))]
        parts.extend(_encode_value(item) for item in value)
        return b"".join(parts)
    if isinstance(value, dict):
        parts = [bytes((_TYPE_DICT,)), _pack_uint32(len(value))]
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("dictionary-keys-must-be-strings")
            parts.append(_encode_value(key))
            parts.append(_encode_value(item))
        return b"".join(parts)
    raise TypeError(f"unsupported-type:{type(value).__name__}")


def _decode_length(buffer, offset):
    end = offset + _UINT32_STRUCT.size
    if end > len(buffer):
        raise ValueError("truncated-length")
    return _UINT32_STRUCT.unpack(buffer[offset:end])[0], end


def _decode_value(buffer, offset=0):
    if offset >= len(buffer):
        raise ValueError("missing-type-tag")

    type_tag = buffer[offset]
    offset += 1

    if type_tag == _TYPE_NONE:
        return None, offset
    if type_tag == _TYPE_FALSE:
        return False, offset
    if type_tag == _TYPE_TRUE:
        return True, offset
    if type_tag == _TYPE_INT:
        end = offset + _INT64_STRUCT.size
        if end > len(buffer):
            raise ValueError("truncated-int")
        return _INT64_STRUCT.unpack(buffer[offset:end])[0], end
    if type_tag == _TYPE_FLOAT:
        end = offset + _FLOAT64_STRUCT.size
        if end > len(buffer):
            raise ValueError("truncated-float")
        return _FLOAT64_STRUCT.unpack(buffer[offset:end])[0], end
    if type_tag in {_TYPE_STRING, _TYPE_BYTES}:
        length, offset = _decode_length(buffer, offset)
        end = offset + length
        if end > len(buffer):
            raise ValueError("truncated-bytes")
        raw = bytes(buffer[offset:end])
        if type_tag == _TYPE_STRING:
            return raw.decode("utf-8"), end
        return raw, end
    if type_tag == _TYPE_LIST:
        count, offset = _decode_length(buffer, offset)
        items = []
        for _ in range(count):
            item, offset = _decode_value(buffer, offset)
            items.append(item)
        return items, offset
    if type_tag == _TYPE_DICT:
        count, offset = _decode_length(buffer, offset)
        items = {}
        for _ in range(count):
            key, offset = _decode_value(buffer, offset)
            if not isinstance(key, str):
                raise ValueError("dictionary-key-must-be-string")
            value, offset = _decode_value(buffer, offset)
            items[key] = value
        return items, offset
    raise ValueError(f"unknown-type-tag:{type_tag}")


def encode_message(message):
    payload = _encode_value(message)
    return _HEADER_STRUCT.pack(_FRAME_MAGIC, len(payload)) + payload


def decode_message(frame):
    message, offset = _decode_value(memoryview(frame), 0)
    if offset != len(frame):
        raise ValueError("unexpected-trailing-bytes")
    if not isinstance(message, dict):
        raise ValueError("message-must-be-dictionary")
    return message


def _recv_exact(client_socket, size):
    chunks = bytearray()
    chunk_sizes = []
    remaining = size
    while remaining > 0:
        chunk = client_socket.recv(remaining)
        if not chunk:
            return (None, chunk_sizes) if not chunks else (bytes(chunks), chunk_sizes)
        chunks.extend(chunk)
        chunk_sizes.append(len(chunk))
        remaining -= len(chunk)
    return bytes(chunks), chunk_sizes


def send_framed_message(client_socket, message):
    frame = encode_message(message)
    total_sent = 0
    chunk_sizes = []

    while total_sent < len(frame):
        sent = client_socket.send(frame[total_sent:])
        if sent == 0:
            raise OSError("socket connection broken")
        total_sent += sent
        chunk_sizes.append(sent)

    _log_send(client_socket, message, len(frame) - _HEADER_STRUCT.size, len(frame), chunk_sizes)


def recv_framed_message(client_socket):
    header, header_chunk_sizes = _recv_exact(client_socket, _HEADER_STRUCT.size)
    if header is None:
        return None
    if len(header) != _HEADER_STRUCT.size:
        raise OSError("incomplete-frame-header")

    magic, payload_size = _HEADER_STRUCT.unpack(header)
    if magic != _FRAME_MAGIC:
        raise ValueError("invalid-frame-magic")

    payload, payload_chunk_sizes = _recv_exact(client_socket, payload_size)
    if payload is None or len(payload) != payload_size:
        raise OSError("incomplete-frame-payload")
    message = decode_message(payload)
    _log_receive(client_socket, message, payload_size, header_chunk_sizes, payload_chunk_sizes)
    return message
