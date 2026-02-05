FROM node:20-slim

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm@9.15.0

# Copy workspace configuration
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./

# Install dependencies at root level
RUN pnpm install --frozen-lockfile

# Copy packages (for workspace dependencies like shared-types)
COPY packages/ ./packages/

# Copy web app
COPY apps/web/ ./apps/web/

# Install all workspace dependencies
WORKDIR /app/apps/web
RUN pnpm install

# Expose port
EXPOSE 3000

# Start development server
CMD ["pnpm", "dev", "--port", "3000"]
