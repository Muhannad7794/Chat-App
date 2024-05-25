# Use an official Node runtime as a parent image
FROM node:18

# Set the working directory to /app
WORKDIR /frontend-dockerized

# Clear npm cache
RUN npm cache clean --force

# Copy package.json and package-lock.json
COPY package*.json ./

# Install project dependencies including Bootstrap, React Bootstrap, Axios, and React Router
RUN npm install && \
    npm install bootstrap react-bootstrap axios react-router-dom

# Copy the current directory contents into the container at /frontend-dockerized
COPY . /frontend-dockerized

# Install any needed packages specified in package.json
RUN npm install

# Make port 3000 available to the world outside this container
EXPOSE 3000

# Run npm start when the container launches
CMD ["npm", "start"]
