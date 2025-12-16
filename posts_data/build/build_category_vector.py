import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

TECH_CATEGORY = {

    "Frontend": [
        "javascript", "typescript", "react", "nextjs", "vue", "nuxt",
        "svelte", "sveltekit", "solidjs", "astro",
        "redux", "zustand", "recoil", "mobx",
        "tailwind css", "styled components", "emotion", "sass", "scss",
        "vite", "webpack", "babel", "esbuild",
        "three js", "d3 js", "chart js", "canvas", "webgl",
        "html5", "css3", "responsive design", "ui ux", "web components"
    ],

    "Backend": [
        "python", "java", "spring", "spring boot",
        "django", "flask", "fastapi",
        "nodejs", "express", "nest js", "deno",
        "go", "gin", "fiber",
        "php", "laravel", "symfony",
        "ruby", "rails",
        "api", "rest api", "graphql",
        "jwt", "oauth", "session", "middleware"
    ],

    "AI/ML": [
        "ai", "machine learning", "deep learning",
        "pytorch", "tensorflow", "keras",
        "transformer", "bert", "gpt", "llm",
        "rnn", "cnn", "lstm", "gan",
        "embedding", "vector database", "faiss", "pinecone",
        "classification", "regression", "clustering",
        "reinforcement learning", "rl", "natural language processing",
        "nlp", "huggingface", "tokenizer", "text generation"
    ],

    "Database": [
        "mysql", "postgresql", "oracle", "mariadb",
        "mongodb", "redis", "cassandra", "dynamodb",
        "elasticsearch", "neo4j", "graph database",
        "sql", "nosql",
        "indexing", "sharding", "replication", "partitioning",
        "stored procedure", "query optimization", "transaction",
        "acid", "cap theorem", "locking", "cache"
    ],

    "DevOps": [
        "docker", "container", "kubernetes", "k8s",
        "aws", "gcp", "azure",
        "terraform", "ansible", "jenkins", "gitlab ci",
        "github actions", "cicd",
        "prometheus", "grafana", "elk stack",
        "nginx", "apache", "load balancer",
        "scaling", "autoscaling", "serverless", "cloudfront",
        "vpc", "s3", "ec2", "lambda"
    ],

    "Mobile": [
        "android", "kotlin", "java",
        "ios", "swift", "swiftui",
        "react native", "expo",
        "flutter", "dart",
        "mobile ui", "mvvm", "mvp",
        "android studio", "xcode",
        "push notification", "mobile performance", "hybrid app"
    ],

    "Security": [
        "owasp", "xss", "csrf",
        "jwt security", "csp", "authentication", "authorization",
        "encryption", "hashing", "salt",
        "ssl", "tls", "https",
        "sql injection", "session hijacking",
        "malware", "ransomware", "phishing",
        "penetration testing", "vulnerability scan",
    ],

    "CS": [
        "algorithm", "data structure",
        "array", "linked list", "stack", "queue",
        "tree", "graph", "dfs", "bfs", "dijkstra",
        "sorting", "searching",
        "operating system", "process", "thread", "semaphore",
        "deadlock", "cpu scheduling",
        "network", "tcp ip", "http", "websocket", "dns",
        "design pattern", "oop", "functional programming"
    ]
}


category_vectors = {}

for cat, words in TECH_CATEGORY.items():
    vecs = model.encode(words)
    category_vectors[cat] = np.mean(vecs, axis=0)

np.save("posts_data/category_vectors.npy", category_vectors)
print("Saved:", list(category_vectors.keys()))
