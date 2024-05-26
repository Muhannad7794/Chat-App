# Use an official Node base image
FROM node:18

# Set the working directory in the container
WORKDIR /frontend-dockerized

# Copy package.json and package-lock.json
COPY package*.json ./

# Copy the current directory contents into the container at /frontend-dockerized
COPY . /frontend-dockerized

# Install any needed packages specified in package.json
RUN npm install

# Make port 3000 available to the world outside this container
EXPOSE 3000

# Run npm start when the container launches
CMD ["npm", "start"]