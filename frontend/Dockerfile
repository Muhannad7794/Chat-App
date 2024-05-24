# Use an official Node base image
FROM node:14

# Set the working directory in the container
WORKDIR /frontend-dockerized

# Copy package.json and package-lock.json
COPY package*.json ./

# Install project dependencies
RUN npm install

# Copy the project files into the container
COPY . .

# Build the app
RUN npm run build

# Install serve to serve the build directory on port 3000
RUN npm install -g serve

# Command to serve the app
CMD ["serve", "-s", "build", "-l", "3000"]
