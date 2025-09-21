const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

class TodoList {
    constructor(name = 'My Todo List') {
        this.name = name;
        this.todos = [];
        this.categories = new Set();
    }

    addTask(task, category = 'general') {
        const newTask = {
            id: crypto.randomUUID(),
            text: task,
            category: category,
            completed: false,
            priority: 'medium',
            createdAt: new Date(),
            tags: []
        };
        this.todos.push(newTask);
        this.categories.add(category);
        return newTask.id;
    }

    completeTask(id) {
        const task = this.todos.find(t => t.id === id);
        if (task) {
            task.completed = true;
            task.completedAt = new Date();
            return true;
        }
        return false;
    }

    setPriority(id, priority) {
        const task = this.todos.find(t => t.id === id);
        if (task && ['low', 'medium', 'high'].includes(priority)) {
            task.priority = priority;
            return true;
        }
        return false;
    }

    addTag(id, tag) {
        const task = this.todos.find(t => t.id === id);
        if (task && !task.tags.includes(tag)) {
            task.tags.push(tag);
            return true;
        }
        return false;
    }

    getPendingTasks() {
        return this.todos.filter(task => !task.completed);
    }

    getCompletedTasks() {
        return this.todos.filter(task => task.completed);
    }

    getTasksByCategory(category) {
        return this.todos.filter(task => task.category === category);
    }

    getTasksByPriority(priority) {
        return this.todos.filter(task => task.priority === priority);
    }
}

async function saveToFile(data, filename) {
    try {
        await fs.writeFile(filename, JSON.stringify(data, null, 2));
        console.log(`Data saved to ${filename}`);
    } catch (error) {
        console.error(`Error saving to ${filename}:`, error);
    }
}

async function loadFromFile(filename) {
    try {
        const data = await fs.readFile(filename, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        console.error(`Error loading from ${filename}:`, error);
        return null;
    }
}

function exportToCSV(tasks, filename) {
    const headers = ['ID', 'Text', 'Category', 'Priority', 'Completed', 'Created At'];
    const rows = tasks.map(task => [
        task.id,
        task.text,
        task.category,
        task.priority,
        task.completed,
        task.createdAt
    ]);

    const csvContent = [headers, ...rows]
        .map(row => row.map(field => `"${field}"`).join(','))
        .join('\n');

    fs.writeFileSync(filename, csvContent);
    console.log(`CSV exported to ${filename}`);
}

module.exports = { TodoList, saveToFile, loadFromFile, exportToCSV };
