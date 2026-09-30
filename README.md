# 🎮 FlowForge – AI Adaptive Dungeon

> A 2D dungeon game built with Python and Pygame that integrates
> Artificial Intelligence concepts such as A* Pathfinding and
> Manhattan Distance for intelligent enemy navigation and player assistance.

---

## 📌 Table of Contents

- [Project Overview](#-project-overview)
- [Problem Statement](#-problem-statement)
- [Objectives](#-objectives)
- [Key Features](#-key-features)
- [AI Concepts](#-ai-concepts)
- [System Architecture](#-system-architecture)
- [System Flow](#-system-flow)
- [Gameplay Flow](#-gameplay-flow)
- [Project Architecture](#-project-architecture)
- [Module Description](#-module-description)
- [Game Controls](#-game-controls)
- [Screenshots](#-screenshots)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Running the Project](#-running-the-project)
- [Project Structure](#-project-structure)
- [Testing](#-testing)
- [Future Scope](#-future-scope)
- [Academic Information](#-academic-information)
- [Conclusion](#-conclusion)

---

# 📌 Project Overview

**FlowForge – AI Adaptive Dungeon** is a 2D dungeon game developed using
**Python and Pygame**.

The project combines game development with basic Artificial Intelligence
concepts to demonstrate how AI algorithms can be integrated into a
real-time game environment.

The main AI component is **A* Pathfinding**, which is used for intelligent
enemy navigation. **Manhattan Distance** is used as the heuristic function
to estimate the distance between an enemy and its target.

The game also provides **AI-based path assistance** to help the player
navigate through the dungeon when required.

The player must explore the dungeon, interact with enemies, collect the
required core and reach the exit to progress through the levels.

---

# 🎯 Problem Statement

Traditional 2D games often use fixed enemy movement and predefined
behaviour.

Such systems may not dynamically determine an efficient path according to
the current position of the player and the environment.

**FlowForge** addresses this problem by integrating AI-based pathfinding
into a real-time 2D dungeon game.

The project demonstrates how an AI algorithm such as A* can be used for
enemy navigation and player assistance.

---

# 🎯 Objectives

The main objectives of FlowForge are:

- Develop a functional 2D dungeon game using Python and Pygame.
- Implement player movement and interaction.
- Implement shooting and dash mechanics.
- Develop different enemy types with different behaviours.
- Implement A* pathfinding for enemy navigation.
- Use Manhattan Distance as the heuristic for A*.
- Implement collision detection and health management.
- Provide AI-based path assistance.
- Implement core collection and exit-based objectives.
- Implement multiple-level gameplay.
- Demonstrate the practical application of AI algorithms in game development.

---

# ✨ Key Features

## 👤 Player

- WASD / Arrow key movement
- Shooting mechanism
- Dash ability
- Health system
- Collision detection
- Core collection
- Exit-based level progression

## 👾 Enemy System

FlowForge contains different enemy types:

| Enemy | Behaviour |
|-------|-----------|
| **Hunter** | Pursues the player using navigation behaviour |
| **Scout** | Faster and lighter enemy behaviour |
| **Tank** | Stronger enemy with greater resistance |

## 🤖 AI Features

- A* Pathfinding
- Manhattan Distance heuristic
- Intelligent enemy navigation
- AI-based path assistance

## 🎮 Game Features

- Multiple dungeon levels
- Enemy attacks and bullets
- Collision detection
- Health management
- Dash mechanics
- Sound effects
- Particle and visual effects
- Core collection
- Level progression
- Win condition

---

# 🧠 AI Concepts

## 1. A* Pathfinding

A* is a pathfinding algorithm used to find an efficient path between a
starting position and a destination.

The evaluation function used by A* is:

```text
f(n) = g(n) + h(n)
