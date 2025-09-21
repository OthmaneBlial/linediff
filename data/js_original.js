const fs = require('fs');
const path = require('path');

class TodoList {
    constructor() {
        this.todos = [];
    }

    addTask(task) {
        this.todos.push({
            id: Date.now(),
            text: task,
            completed: false,
            createdAt: new Date()
        });
    }

    completeTask(id) {
        const task = this.todos.find(t => t.id === id);
        if (task) {
            task.completed = true;
            task.completedAt = new Date();
        }
    }

    getPendingTasks() {
        return this.todos.filter(task => !task.completed);
    }

    getCompletedTasks() {
        return this.todos.filter(task => task.completed);
    }
}

function saveToFile(data, filename) {
    try {
        fs.writeFileSync(filename, JSON.stringify(data, null, 2));
        console.log(`Data saved to ${filename}`);
    } catch (error) {
        console.error(`Error saving to ${filename}:`, error);
    }
}

function loadFromFile(filename) {
    try {
        const data = fs.readFileSync(filename, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        console.error(`Error loading from ${filename}:`, error);
        return null;
    }
}

module.exports = { TodoList, saveToFile, loadFromFile };
