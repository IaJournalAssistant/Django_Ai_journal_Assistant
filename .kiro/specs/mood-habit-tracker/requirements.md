# Requirements Document

## Introduction

A simple mood and habit tracker integrated into the existing Django journal application that allows users to log their daily moods, track habits, and gain insights through AI-powered analysis. The system will use an open-source AI model to provide personalized insights while maintaining simplicity and avoiding over-engineering.

## Glossary

- **Mood Tracker System**: The Django application component that handles mood logging and analysis
- **Habit Tracker System**: The Django application component that manages habit creation, tracking, and progress monitoring
- **AI Analysis Engine**: The open-source AI model integration that provides insights and recommendations
- **User**: An authenticated person using the mood and habit tracking features
- **Mood Entry**: A single record of a user's emotional state at a specific time
- **Habit**: A recurring activity or behavior that a user wants to track
- **Habit Log**: A record of habit completion or non-completion for a specific date
- **Insight**: AI-generated analysis or recommendation based on mood and habit data

## Requirements

### Requirement 1

**User Story:** As a user, I want to log my daily mood, so that I can track my emotional patterns over time

#### Acceptance Criteria

1. WHEN a user accesses the mood logging interface, THE Mood Tracker System SHALL display a simple mood selection interface with predefined mood options
2. WHEN a user selects a mood and submits the entry, THE Mood Tracker System SHALL store the mood entry with timestamp and user association
3. THE Mood Tracker System SHALL allow only one mood entry per day per user
4. WHEN a user has already logged a mood for the current day, THE Mood Tracker System SHALL display the existing entry and allow modification
5. THE Mood Tracker System SHALL provide a visual mood history showing the last 30 days of mood entries

### Requirement 2

**User Story:** As a user, I want to create and track daily habits, so that I can build positive routines and monitor my progress

#### Acceptance Criteria

1. THE Habit Tracker System SHALL allow users to create custom habits with a name and optional description
2. WHEN a user creates a habit, THE Habit Tracker System SHALL set the habit as active by default
3. THE Habit Tracker System SHALL display a daily habit checklist showing all active habits
4. WHEN a user marks a habit as completed for a day, THE Habit Tracker System SHALL record the completion with timestamp
5. THE Habit Tracker System SHALL calculate and display completion streaks for each habit

### Requirement 3

**User Story:** As a user, I want to see my mood and habit patterns, so that I can understand correlations and trends in my behavior

#### Acceptance Criteria

1. THE Mood Tracker System SHALL display a weekly mood trend chart showing mood patterns
2. THE Habit Tracker System SHALL show completion percentages for each habit over the last 7 and 30 days
3. WHEN a user views their dashboard, THE Mood Tracker System SHALL display the current mood streak (consecutive days of logging)
4. THE Habit Tracker System SHALL highlight habits with the longest current streaks
5. THE Mood Tracker System SHALL provide a simple calendar view showing mood entries for the current month

### Requirement 4

**User Story:** As a user, I want AI-powered insights about my mood and habit patterns, so that I can receive personalized recommendations for improvement

#### Acceptance Criteria

1. WHEN a user has at least 7 days of mood and habit data, THE AI Analysis Engine SHALL generate weekly insights
2. THE AI Analysis Engine SHALL identify correlations between habit completion and mood patterns
3. THE AI Analysis Engine SHALL provide actionable recommendations based on user patterns
4. THE AI Analysis Engine SHALL use only open-source models for analysis to ensure privacy and cost-effectiveness
5. WHEN generating insights, THE AI Analysis Engine SHALL process data locally without sending personal information to external services

### Requirement 5

**User Story:** As a user, I want the mood and habit tracker to integrate seamlessly with my existing journal, so that I have a unified personal tracking experience

#### Acceptance Criteria

1. THE Mood Tracker System SHALL integrate with the existing Django user authentication system
2. THE Habit Tracker System SHALL use the same UI design patterns as the existing journal application
3. WHEN a user navigates between journal and tracking features, THE Mood Tracker System SHALL maintain consistent navigation and styling
4. THE Mood Tracker System SHALL be accessible from the main application navigation
5. THE Habit Tracker System SHALL store data in the same database as the existing journal application