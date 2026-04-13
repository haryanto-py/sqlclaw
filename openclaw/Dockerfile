# OpenClaw agent — Node.js 20
FROM node:20-alpine

WORKDIR /app

# Install OpenClaw globally
RUN npm install -g openclaw

# Install the PostgreSQL clawhub skill into the global OpenClaw skills directory
RUN npx clawhub@latest install postgresql

# Copy agent config and local skills
COPY . .

CMD ["openclaw", "start", "--config", "./openclaw.json"]
