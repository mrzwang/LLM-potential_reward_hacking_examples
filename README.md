# In-Context-Learning-for-Esoteric-Programming-Languages Potential Reward Hacking Examples

This repository contains examples of **reward hacking** discovered within the In Context Learning for Esoteric Programming Languages Project that occured in agentic code-writing systems:  specifically when tasked with solving code problems in **esoteric programming languages** against a defined suite of test cases.

These examples were generated and curated during research into the transfer learning ability of large language models and agentic AIs to write code in esoteric coding languages.

## Repo Structure

.
├── evaluation_scripts/ # Tools and scripts to evaluate model outputs
├── examples/ # Concrete examples of reward hacking behavior
├── .gitignore
└── README.md 

## Purpose

Language models, especially agentic systems often optimize for automated reward functions such as "passes all test cases." This repository provides artifacts during our study showing how models exploit edge cases in the reward function to succeed without truly solving the task.

These behaviors:
- Occur more frequently in **agentic setups** (multi-step planning or feedback loops)
- Appear when code is written in **unusual or adversarial programming languages**
- Can lead to false confidence in system capability or alignment

## Examples Include

- Crafting misleading outputs that match test outputs by accident
- Abuse of language-specific quirks (e.g., infinite loops with no error)
- Partial hardcoding of test cases disguised as general solutions

## Use Cases

- **Research**: Analyzing failure modes in LLMs under reward-based fine-tuning
- **Diagnostics**: Stress-testing reward functions for loopholes
- **Education**: Teaching the risks of over-optimizing weak reward signals

## Note

This repository is a **snapshot of research artifacts** and is not actively maintained. It was originally developed during an investigation into reward hacking in self-improving agents.
