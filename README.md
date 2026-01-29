# Slack Messaging Prioritization App 📬

A powerful Slack application that automatically detects and helps you prioritize messages based on urgency and importance. This app uses intelligent keyword detection and provides interactive tools to manage message priorities effectively.

## ✨ Features

### 🤖 Automatic Priority Detection
- Automatically detects message priority based on configurable keywords
- Instantly tags messages with colored emoji reactions
- Supports four priority levels: Critical, High, Medium, and Low

### 🎯 Manual Prioritization
- Use `/prioritize` command to manually tag your messages
- Interactive button interface for easy priority selection
- Apply priorities retroactively to recent messages

### 📊 Visual Indicators
- **🔴 Critical** - Urgent issues requiring immediate attention (red circle)
- **🟠 High** - Important tasks with deadlines (orange circle)
- **🟡 Medium** - Standard priority items (yellow circle)
- **🟢 Low** - Informational updates and FYIs (green circle)

### 🏠 App Home Dashboard
- View priority levels and their meanings
- Quick access to available commands
- User-friendly interface for understanding the app

## 🚀 Quick Start

### Prerequisites
- Node.js 16.0 or higher
- A Slack workspace where you can install apps
- Admin access to create Slack apps

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/chenggong-zhang/slack_api.git
   cd slack_api
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Create a Slack App**
   - Go to [api.slack.com/apps](https://api.slack.com/apps)
   - Click "Create New App" → "From scratch"
   - Name your app (e.g., "Message Prioritization")
   - Select your workspace

4. **Configure your Slack App**

   **Enable Socket Mode:**
   - Go to "Socket Mode" in the sidebar
   - Enable Socket Mode
   - Generate an App-Level Token with `connections:write` scope
   - Save the token (starts with `xapp-`)

   **Add Bot Token Scopes:**
   - Go to "OAuth & Permissions"
   - Add the following Bot Token Scopes:
     - `chat:write` - Send messages
     - `reactions:write` - Add emoji reactions
     - `channels:history` - View messages in public channels
     - `groups:history` - View messages in private channels
     - `im:history` - View messages in DMs
     - `mpim:history` - View messages in group DMs
     - `commands` - Create slash commands
   - Install the app to your workspace
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)

   **Enable Events:**
   - Go to "Event Subscriptions"
   - Enable Events
   - Subscribe to bot events:
     - `message.channels` - Listen to channel messages
     - `message.groups` - Listen to private channel messages
     - `message.im` - Listen to DM messages
     - `message.mpim` - Listen to group DM messages
     - `app_home_opened` - App Home tab

   **Create Slash Commands:**
   - Go to "Slash Commands"
   - Create `/prioritize` command
     - Command: `/prioritize`
     - Short Description: "Manually prioritize your last message"
     - Usage Hint: "Set priority for your recent message"
   - Create `/priority-keywords` command
     - Command: `/priority-keywords`
     - Short Description: "View priority detection keywords"
     - Usage Hint: "Display configured priority keywords"

   **Get Signing Secret:**
   - Go to "Basic Information"
   - Copy the "Signing Secret"

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   ```env
   SLACK_BOT_TOKEN=xoxb-your-bot-token-here
   SLACK_SIGNING_SECRET=your-signing-secret-here
   SLACK_APP_TOKEN=xapp-your-app-token-here
   ```

6. **Customize priority keywords (optional)**
   
   Edit the keyword lists in `.env` to match your team's terminology:
   ```env
   CRITICAL_KEYWORDS=urgent,emergency,critical,asap,immediately
   HIGH_KEYWORDS=important,priority,deadline,blocker
   MEDIUM_KEYWORDS=soon,needed,required
   LOW_KEYWORDS=fyi,info,update
   ```

7. **Start the application**
   ```bash
   npm start
   ```
   
   Or for development with auto-restart:
   ```bash
   npm run dev
   ```

## 💡 Usage

### Automatic Priority Detection
Simply send messages containing priority keywords. The app will automatically add the appropriate emoji reaction:

```
"This is an urgent bug in production!" → 🔴 Critical
"Important deadline next week" → 🟠 High
"This is needed soon" → 🟡 Medium
"FYI: New documentation available" → 🟢 Low
```

### Manual Prioritization
1. Send a message in any channel where the bot is present
2. Type `/prioritize` in the same channel
3. Click the button for your desired priority level
4. The bot will add the corresponding emoji reaction to your last message

### View Priority Keywords
- Type `/priority-keywords` to see all configured keywords
- This helps team members understand how automatic detection works

### App Home
- Click on the app name in the sidebar
- View the dashboard with priority information and commands
- Get quick help on how to use the app

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SLACK_BOT_TOKEN` | Bot User OAuth Token from Slack | Yes |
| `SLACK_SIGNING_SECRET` | Signing Secret from Slack | Yes |
| `SLACK_APP_TOKEN` | App-Level Token for Socket Mode | Yes |
| `CRITICAL_KEYWORDS` | Comma-separated critical keywords | No |
| `HIGH_KEYWORDS` | Comma-separated high priority keywords | No |
| `MEDIUM_KEYWORDS` | Comma-separated medium priority keywords | No |
| `LOW_KEYWORDS` | Comma-separated low priority keywords | No |

### Priority Levels

The app supports four priority levels, each with its own emoji indicator:

| Level | Emoji | Reaction Name | Use Case |
|-------|-------|---------------|----------|
| Critical | 🔴 | red_circle | Urgent issues, emergencies, immediate action required |
| High | 🟠 | orange_circle | Important tasks, approaching deadlines, blockers |
| Medium | 🟡 | yellow_circle | Standard priority, should be addressed soon |
| Low | 🟢 | green_circle | Informational, FYI, no immediate action needed |

## 🏗️ Architecture

### Technology Stack
- **Runtime:** Node.js 16+
- **Framework:** @slack/bolt (Slack Bolt Framework)
- **Communication:** Socket Mode (no public URL required)
- **Configuration:** dotenv for environment variables

### Core Components

1. **Message Listener:** Monitors all incoming messages for priority keywords
2. **Priority Detector:** Analyzes message content and assigns priority levels
3. **Reaction Manager:** Adds/manages emoji reactions on messages
4. **Command Handlers:** Processes slash commands (`/prioritize`, `/priority-keywords`)
5. **Interactive Components:** Handles button clicks for manual prioritization
6. **App Home:** Provides a user dashboard with app information

### How It Works

```
User Message → Priority Detection → Auto-tagging → Emoji Reaction
                      ↓
              Manual Override → Button UI → Priority Selection → Emoji Reaction
```

## 🧪 Development

### Running in Development Mode
```bash
npm run dev
```

This uses `nodemon` to automatically restart the app when you make changes to the code.

### Running Tests
```bash
npm test
```

This runs the unit tests to verify the priority detection logic and environment validation.

### Project Structure
```
slack_api/
├── app.js              # Main application file
├── test.js             # Unit tests
├── package.json        # Dependencies and scripts
├── .env.example        # Example environment configuration
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## 🤝 Contributing

Contributions are welcome! Here are some ways you can contribute:

1. **Add new features:**
   - Scheduled priority summaries
   - Priority-based message filtering
   - Custom priority levels
   - Integration with task management tools

2. **Improve detection:**
   - Machine learning-based priority detection
   - User-specific priority rules
   - Channel-specific configurations

3. **Enhance UI:**
   - More interactive components
   - Rich App Home with statistics
   - Priority analytics dashboard

## 📝 License

MIT License - feel free to use this project for personal or commercial purposes.

## 🐛 Troubleshooting

### App doesn't respond to messages
- Ensure the bot is invited to the channel (`/invite @YourBotName`)
- Check that event subscriptions are properly configured
- Verify Socket Mode is enabled

### Slash commands not working
- Confirm commands are created in the Slack App settings
- Ensure the app is installed in your workspace
- Check that command names match exactly

### Reactions not appearing
- Verify the bot has `reactions:write` permission
- Check that the bot has access to message history
- Ensure emoji names are correct in the code

### Environment variable issues
- Confirm `.env` file exists and is in the project root
- Check that all required tokens are properly set
- Verify token formats (xoxb-, xapp-, etc.)

## 🔗 Resources

- [Slack Bolt Framework Documentation](https://slack.dev/bolt-js/)
- [Slack API Documentation](https://api.slack.com/)
- [Socket Mode Guide](https://api.slack.com/apis/connections/socket)
- [Building Slack Apps Tutorial](https://api.slack.com/start/building)

## 📧 Support

For issues, questions, or suggestions, please open an issue in the GitHub repository.

---

Made with ❤️ for better Slack communication