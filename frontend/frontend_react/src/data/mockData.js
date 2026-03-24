export const landingFeatures = [
  {
    title: "Real-time Ranking",
    description: "Watch live leaderboards update instantly as participants answer questions."
  },
  {
    title: "Multiple Participants",
    description: "Host classrooms, team rounds, or larger training sessions with ease."
  },
  {
    title: "Domain-based Quizzes",
    description: "Create topic-focused quizzes and tailor difficulty for every audience."
  },
  {
    title: "Fair Timed System",
    description: "Keep quizzes synchronized so each participant gets equal time."
  }
];

export const adminStats = [
  { label: "Total Quizzes", value: "24", trend: "+12% from last month" },
  { label: "Active Users", value: "1,247", trend: "+8% from last week" },
  { label: "Completion Rate", value: "87.5%", trend: "-2% from last month" }
];

export const recentQuizzes = [
  { name: "JavaScript Fundamentals", type: "Public", participants: 156, status: "Active" },
  { name: "React Components Quiz", type: "Private", participants: 23, status: "Draft" },
  { name: "Python Basics", type: "Public", participants: 89, status: "Ended" }
];

export const publicQuizzes = [
  { quizId: "PUB-101", title: "Advanced JavaScript Patterns", owner: "Admin", plays: "20k", category: "Programming", quizType: "public" },
  { quizId: "PUB-102", title: "Network Security Fundamentals", owner: "System Owner", plays: "15k", category: "Networking", quizType: "public" },
  { quizId: "PUB-103", title: "World Geography Masterclass", owner: "Admin", plays: "10k", category: "General Knowledge", quizType: "public" }
];

export const categories = [
  { title: "Programming", count: 12 },
  { title: "Networking", count: 8 },
  { title: "General Knowledge", count: 7 }
];

export const leaderboardTopThree = [
  { name: "Sarah Jenkins", score: 985, rank: 2, time: "18m 27s" },
  { name: "Michael Chen", score: 998, rank: 1, time: "17m 45s" },
  { name: "Elena Rodriguez", score: 972, rank: 3, time: "18m 55s" }
];

export const leaderboardRows = [
  { rank: 4, name: "David Wilson", score: 965, completion: "18m 45s", status: "Verified" },
  { rank: 5, name: "Sophie Turner", score: 958, completion: "17m 12s", status: "Verified" },
  { rank: 12, name: "Alex Johnson (You)", score: 912, completion: "19m 55s", status: "Current User" },
  { rank: 13, name: "James Allen", score: 908, completion: "20m 05s", status: "Verified" },
  { rank: 14, name: "Lily Wong", score: 895, completion: "20m 30s", status: "Verified" }
];

export const questions = Array.from({ length: 20 }, (_, index) => index + 1);
