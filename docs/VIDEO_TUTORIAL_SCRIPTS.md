# CodeGenie Video Tutorial Scripts

This document contains scripts for creating video tutorials about CodeGenie features.

## Table of Contents
1. [Getting Started (5 minutes)](#getting-started)
2. [Building Your First API (10 minutes)](#building-your-first-api)
3. [Autonomous Development (8 minutes)](#autonomous-development)
4. [Multi-Agent Collaboration (12 minutes)](#multi-agent-collaboration)
5. [Advanced Refactoring (10 minutes)](#advanced-refactoring)
6. [Testing Automation (7 minutes)](#testing-automation)

---

## Getting Started

**Duration:** 5 minutes  
**Target Audience:** Beginners  
**Prerequisites:** None

### Script

**[00:00 - 00:30] Introduction**

> "Hi! Welcome to CodeGenie. I'm going to show you how to get started with your AI-powered coding assistant in just 5 minutes."

**[00:30 - 01:30] Installation**

> "First, let's install CodeGenie. You'll need Python 3.9 or higher and Ollama for running AI models locally."

**Screen:** Show terminal

```bash
# Clone repository
git clone https://github.com/your-org/codegenie.git
cd codegenie

# Run quick start
./quick_start.sh
```

> "The quick start script will set everything up for you - creating a virtual environment, installing dependencies, and downloading AI models."

**[01:30 - 02:30] First Command**

> "Now let's try our first command. I'll start CodeGenie and ask it to create a simple function."

**Screen:** Show CodeGenie interface

```
You: Create a Python function to calculate fibonacci numbers

CodeGenie: I'll create a fibonacci function for you...
```

> "Notice how CodeGenie understands what I want and creates not just the function, but also includes proper documentation and type hints."

**[02:30 - 03:30] Interactive Features**

> "CodeGenie is interactive. I can ask it to modify the code, add tests, or explain how it works."

```
You: Add memoization to make it faster

CodeGenie: I'll add memoization using functools.lru_cache...
```

> "See how it understood my request and improved the code? That's the power of CodeGenie."

**[03:30 - 04:30] Getting Help**

> "If you ever need help, just type 'help' to see available commands."

**Screen:** Show help output

> "You can also ask CodeGenie questions about your code, request reviews, or get debugging help."

**[04:30 - 05:00] Wrap Up**

> "That's it! You're now ready to use CodeGenie. In the next video, we'll build a complete REST API together. Thanks for watching!"

### Recording Notes

- Use screen recording software (OBS, ScreenFlow, Camtasia)
- Record at 1920x1080 resolution
- Use clear, large terminal font (18-20pt)
- Add captions for accessibility
- Include chapter markers at each timestamp

### Assets Needed

- CodeGenie logo for intro/outro
- Background music (optional, low volume)
- Terminal theme with good contrast
- Prepared demo environment

---

## Building Your First API

**Duration:** 10 minutes  
**Target Audience:** Beginners to Intermediate  
**Prerequisites:** Basic Python knowledge

### Script

**[00:00 - 00:45] Introduction**

> "In this tutorial, we'll build a complete REST API with authentication, database integration, and tests - all in under 10 minutes using CodeGenie."

**[00:45 - 02:00] Project Setup**

> "Let's start by asking CodeGenie to create a FastAPI project."

```
You: Create a FastAPI project for a todo list application with user authentication

CodeGenie: I'll create a complete todo API for you...
```

> "CodeGenie is now creating the entire project structure, setting up the database, and implementing authentication. Let's watch as it works."

**Screen:** Show progress as CodeGenie creates files

**[02:00 - 03:30] Exploring the Code**

> "Let's look at what CodeGenie created. We have a clean project structure with models, API endpoints, services, and tests."

**Screen:** Navigate through project structure

> "Notice how it follows best practices - dependency injection, proper separation of concerns, and comprehensive error handling."

**[03:30 - 05:00] Running the API**

> "Let's start the server and test it out."

```bash
uvicorn src.main:app --reload
```

**Screen:** Show API documentation at /docs

> "CodeGenie automatically generated interactive API documentation. Let's try creating a user and a todo item."

**[05:00 - 06:30] Adding Features**

> "Now let's add a new feature. I want users to be able to share their todo lists."

```
You: Add functionality for users to share their todo lists with other users

CodeGenie: I'll add sharing functionality...
```

> "Watch as CodeGenie adds the new models, endpoints, and tests for the sharing feature."

**[06:30 - 08:00] Testing**

> "Let's run the tests to make sure everything works."

```bash
pytest tests/ -v
```

**Screen:** Show tests passing

> "All tests pass! CodeGenie created comprehensive tests for all the functionality."

**[08:00 - 09:30] Code Review**

> "Let's ask CodeGenie to review the code for any issues."

```
You: Review the code for security issues

CodeGenie: Analyzing security...
```

> "CodeGenie found a few recommendations and can automatically fix them. This is great for maintaining code quality."

**[09:30 - 10:00] Wrap Up**

> "In just 10 minutes, we built a complete, production-ready API with authentication, CRUD operations, sharing, and tests. Try it yourself and see what you can build!"

### Recording Notes

- Split screen: terminal + code editor
- Highlight important code sections
- Speed up file creation sequences (2x)
- Add annotations for key concepts
- Include timestamps in description

---

## Autonomous Development

**Duration:** 8 minutes  
**Target Audience:** Intermediate  
**Prerequisites:** Basic CodeGenie usage

### Script

**[00:00 - 00:30] Introduction**

> "Autonomous mode is CodeGenie's most powerful feature. It can build entire features with minimal supervision. Let me show you how."

**[00:30 - 01:30] Enabling Autonomous Mode**

> "First, let's enable autonomous mode."

```
You: /autonomous on

CodeGenie: Autonomous mode enabled...
```

> "In autonomous mode, CodeGenie will break down complex tasks, make decisions automatically, and execute multiple steps without asking for approval each time."

**[01:30 - 03:00] Defining the Goal**

> "Let's give CodeGenie a complex task - building a complete comment system with nested replies, likes, and moderation."

```
You: Build a complete comment system for blog posts with nested replies, likes, and admin moderation features

CodeGenie: Analyzing requirements...
```

**Screen:** Show execution plan

> "CodeGenie created a 20-step plan. It will design the architecture, create models, implement endpoints, add tests, and more."

**[03:00 - 05:30] Watching Execution**

> "Now watch as CodeGenie works autonomously."

**Screen:** Show progress through steps

> "Notice the intervention points where we can review progress. CodeGenie is making intelligent decisions about implementation details."

**[05:30 - 06:30] Intervention Point**

> "Here's an intervention point. CodeGenie is asking about moderation features."

```
CodeGenie: Should I add:
A. Bulk moderation actions
B. Moderation logs
C. Auto-moderation rules
D. All of the above

You: D
```

> "I can guide the implementation at key decision points while CodeGenie handles the details."

**[06:30 - 07:30] Completion**

> "And we're done! CodeGenie built the entire feature in about 30 minutes of autonomous work."

**Screen:** Show summary

> "We have 12 new files, 45 tests all passing, and complete documentation. All from a single request."

**[07:30 - 08:00] Wrap Up**

> "Autonomous mode is perfect for building features quickly while maintaining quality. Try it for your next project!"

### Recording Notes

- Time-lapse the execution (show key moments)
- Highlight decision points
- Show before/after comparison
- Include metrics (files created, tests, time)

---

## Multi-Agent Collaboration

**Duration:** 12 minutes  
**Target Audience:** Advanced  
**Prerequisites:** Understanding of software architecture

### Script

**[00:00 - 00:45] Introduction**

> "CodeGenie includes specialized agents for different aspects of development. In this video, we'll see how they collaborate to build a payment processing system."

**[00:45 - 02:00] The Agents**

> "Let me introduce the agents we'll use:"

**Screen:** Show agent descriptions

- Architect Agent: Designs system architecture
- Developer Agent: Implements code
- Security Agent: Ensures security best practices
- Performance Agent: Optimizes performance
- Testing Agent: Creates comprehensive tests
- Documentation Agent: Generates documentation

**[02:00 - 03:30] Starting the Project**

> "Let's ask CodeGenie to build a payment processing feature using all agents."

```
You: Build a payment processing feature with all best practices

CodeGenie: This requires multiple agents. Coordinating...
```

**Screen:** Show agent coordination plan

**[03:30 - 05:00] Architect Agent**

> "First, the Architect Agent designs the system."

**Screen:** Show architecture design

> "It's designed a robust payment flow with proper state management, idempotency, and error handling."

**[05:00 - 06:30] Developer Agent**

> "Now the Developer Agent implements the design."

**Screen:** Show code being created

> "It's creating models, services, and API endpoints following the architecture."

**[06:30 - 08:00] Security Agent**

> "The Security Agent reviews and hardens the implementation."

**Screen:** Show security improvements

> "It's adding encryption, PCI compliance checks, fraud detection, and audit logging."

**[08:00 - 09:30] Performance & Testing Agents**

> "The Performance Agent optimizes the code while the Testing Agent creates tests."

**Screen:** Show optimizations and tests

> "We now have async processing, connection pooling, and 48 comprehensive tests."

**[09:30 - 10:30] Documentation Agent**

> "Finally, the Documentation Agent generates complete documentation."

**Screen:** Show generated docs

> "API docs, integration guides, security documentation - everything we need."

**[10:30 - 11:30] Review**

> "Let's review what the agents built together."

**Screen:** Show final result

> "A production-ready payment system with security, performance, tests, and documentation - all from agent collaboration."

**[11:30 - 12:00] Wrap Up**

> "Multi-agent collaboration is perfect for complex features that need expertise in multiple areas. Each agent brings specialized knowledge to create better software."

### Recording Notes

- Use split screen to show multiple agents
- Color-code each agent's work
- Show agent communication
- Include architecture diagrams
- Add agent "avatars" or icons

---

## Advanced Refactoring

**Duration:** 10 minutes  
**Target Audience:** Intermediate to Advanced  
**Prerequisites:** Understanding of design patterns

### Script

**[00:00 - 00:30] Introduction**

> "In this video, we'll refactor a messy codebase using CodeGenie. We'll extract service layers, implement dependency injection, and improve testability."

**[00:30 - 02:00] The Problem**

> "Here's our starting point - a controller with business logic, database access, and multiple responsibilities."

**Screen:** Show problematic code

> "This violates several SOLID principles and is hard to test. Let's fix it."

**[02:00 - 03:30] Analysis**

> "First, let's ask CodeGenie to analyze the code."

```
You: Analyze this code and suggest improvements

CodeGenie: Analyzing...
```

**Screen:** Show analysis results

> "CodeGenie identified the issues and suggested a refactoring plan."

**[03:30 - 05:30] Service Layer Extraction**

> "Let's extract a service layer."

```
You: Refactor to use a service layer with dependency injection

CodeGenie: Refactoring...
```

**Screen:** Show refactoring in progress

> "CodeGenie is creating service classes, updating the controller, and modifying tests."

**[05:30 - 07:00] Repository Pattern**

> "Now let's add a repository layer for database access."

```
You: Extract a repository layer for database operations

CodeGenie: Creating repository layer...
```

**Screen:** Show repository implementation

**[07:00 - 08:30] Testing the Refactoring**

> "Let's verify everything still works."

```bash
pytest tests/ -v
```

**Screen:** Show tests passing

> "All tests pass! The refactoring maintained functionality while improving structure."

**[08:30 - 09:30] Before and After**

> "Let's compare before and after."

**Screen:** Side-by-side comparison

> "The code is now cleaner, more testable, and follows SOLID principles."

**[09:30 - 10:00] Wrap Up**

> "CodeGenie makes refactoring safe and easy. It understands design patterns and can transform your code while maintaining functionality."

### Recording Notes

- Use diff view to show changes
- Highlight design patterns
- Show test coverage improvements
- Include code metrics (complexity, maintainability)

---

## Testing Automation

**Duration:** 7 minutes  
**Target Audience:** All levels  
**Prerequisites:** Basic testing knowledge

### Script

**[00:00 - 00:30] Introduction**

> "Let's set up a complete automated testing workflow with CodeGenie - from pre-commit hooks to CI/CD."

**[00:30 - 02:00] Setup**

> "I'll ask CodeGenie to set up everything."

```
You: Set up automated testing with pre-commit hooks, coverage checking, and CI/CD

CodeGenie: Setting up testing workflow...
```

**Screen:** Show setup progress

**[02:00 - 03:30] Pre-Commit Hooks**

> "CodeGenie installed pre-commit hooks that run automatically."

**Screen:** Make a commit, show hooks running

> "Before each commit, code is formatted, linted, and tested automatically."

**[03:30 - 05:00] Coverage Reports**

> "Let's check our test coverage."

```bash
pytest --cov=src --cov-report=html
```

**Screen:** Show coverage report

> "We have 94% coverage. CodeGenie can help us reach 100%."

**[05:00 - 06:00] CI/CD Integration**

> "CodeGenie also set up GitHub Actions for continuous integration."

**Screen:** Show GitHub Actions workflow

> "Tests run automatically on every push, ensuring code quality."

**[06:00 - 06:30] Adding Tests**

> "Let's add tests for uncovered code."

```
You: Add tests for the missing coverage in auth service

CodeGenie: Creating tests...
```

**[06:30 - 07:00] Wrap Up**

> "With automated testing, you catch bugs early and maintain high code quality. CodeGenie makes it easy to set up and maintain."

### Recording Notes

- Show real git workflow
- Include GitHub Actions dashboard
- Display coverage trends
- Show test failure and fix

---

## Production Notes

### Equipment

- **Screen Recording**: OBS Studio or ScreenFlow
- **Audio**: Good quality microphone (Blue Yeti, Rode NT-USB)
- **Video Editing**: DaVinci Resolve, Final Cut Pro, or Adobe Premiere

### Recording Settings

- **Resolution**: 1920x1080 (1080p)
- **Frame Rate**: 30 fps
- **Audio**: 48kHz, 16-bit
- **Format**: MP4 (H.264)

### Terminal Setup

- **Font**: Fira Code or JetBrains Mono, 18-20pt
- **Theme**: High contrast (Dracula, Solarized Dark)
- **Window Size**: 120x30 characters
- **Prompt**: Simple, clean prompt

### Editing Checklist

- [ ] Add intro/outro with logo
- [ ] Include chapter markers
- [ ] Add captions/subtitles
- [ ] Remove long pauses
- [ ] Speed up slow sections (1.5-2x)
- [ ] Add annotations for key points
- [ ] Include links in description
- [ ] Add timestamps in description
- [ ] Export in multiple resolutions (1080p, 720p, 480p)

### Publishing

- **Platform**: YouTube, Vimeo
- **Thumbnail**: Custom thumbnail with title
- **Title**: Clear, descriptive, includes "CodeGenie"
- **Description**: Include timestamps, links, prerequisites
- **Tags**: Relevant keywords
- **Playlist**: Organize by topic/difficulty

### Accessibility

- [ ] Add closed captions
- [ ] Include transcript in description
- [ ] Use high contrast visuals
- [ ] Describe visual elements verbally
- [ ] Provide alternative text formats

