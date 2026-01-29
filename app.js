require('dotenv').config();
const { App } = require('@slack/bolt');

// Initialize the Slack app with Socket Mode
const app = new App({
  token: process.env.SLACK_BOT_TOKEN,
  signingSecret: process.env.SLACK_SIGNING_SECRET,
  socketMode: true,
  appToken: process.env.SLACK_APP_TOKEN,
  port: process.env.PORT || 3000
});

// Priority levels with their corresponding emoji reactions
const PRIORITY_LEVELS = {
  CRITICAL: { name: 'critical', emoji: '🔴', reaction: 'red_circle' },
  HIGH: { name: 'high', emoji: '🟠', reaction: 'orange_circle' },
  MEDIUM: { name: 'medium', emoji: '🟡', reaction: 'yellow_circle' },
  LOW: { name: 'low', emoji: '🟢', reaction: 'green_circle' }
};

// Load priority keywords from environment variables
const PRIORITY_KEYWORDS = {
  CRITICAL: (process.env.CRITICAL_KEYWORDS || 'urgent,emergency,critical,asap,immediately').split(',').map(k => k.trim().toLowerCase()),
  HIGH: (process.env.HIGH_KEYWORDS || 'important,priority,deadline,blocker').split(',').map(k => k.trim().toLowerCase()),
  MEDIUM: (process.env.MEDIUM_KEYWORDS || 'soon,needed,required').split(',').map(k => k.trim().toLowerCase()),
  LOW: (process.env.LOW_KEYWORDS || 'fyi,info,update').split(',').map(k => k.trim().toLowerCase())
};

/**
 * Detect priority level based on message content
 * @param {string} text - Message text to analyze
 * @returns {string|null} - Priority level or null if none detected
 */
function detectPriority(text) {
  const lowerText = text.toLowerCase();
  
  // Check for critical keywords first
  if (PRIORITY_KEYWORDS.CRITICAL.some(keyword => lowerText.includes(keyword))) {
    return 'CRITICAL';
  }
  
  // Check for high priority keywords
  if (PRIORITY_KEYWORDS.HIGH.some(keyword => lowerText.includes(keyword))) {
    return 'HIGH';
  }
  
  // Check for medium priority keywords
  if (PRIORITY_KEYWORDS.MEDIUM.some(keyword => lowerText.includes(keyword))) {
    return 'MEDIUM';
  }
  
  // Check for low priority keywords
  if (PRIORITY_KEYWORDS.LOW.some(keyword => lowerText.includes(keyword))) {
    return 'LOW';
  }
  
  return null;
}

/**
 * Add priority reaction to a message
 * @param {Object} client - Slack Web API client
 * @param {string} channel - Channel ID
 * @param {string} timestamp - Message timestamp
 * @param {string} priority - Priority level
 */
async function addPriorityReaction(client, channel, timestamp, priority) {
  try {
    const priorityLevel = PRIORITY_LEVELS[priority];
    if (priorityLevel) {
      await client.reactions.add({
        channel: channel,
        timestamp: timestamp,
        name: priorityLevel.reaction
      });
      console.log(`Added ${priority} priority reaction to message`);
    }
  } catch (error) {
    console.error('Error adding reaction:', error);
  }
}

/**
 * Create interactive buttons for manual priority assignment
 * @returns {Array} - Array of button blocks
 */
function createPriorityButtons() {
  return [
    {
      type: 'section',
      text: {
        type: 'mrkdwn',
        text: '*Set Message Priority:*'
      }
    },
    {
      type: 'actions',
      elements: [
        {
          type: 'button',
          text: {
            type: 'plain_text',
            text: `${PRIORITY_LEVELS.CRITICAL.emoji} Critical`
          },
          action_id: 'priority_critical',
          style: 'danger'
        },
        {
          type: 'button',
          text: {
            type: 'plain_text',
            text: `${PRIORITY_LEVELS.HIGH.emoji} High`
          },
          action_id: 'priority_high',
          style: 'primary'
        },
        {
          type: 'button',
          text: {
            type: 'plain_text',
            text: `${PRIORITY_LEVELS.MEDIUM.emoji} Medium`
          },
          action_id: 'priority_medium'
        },
        {
          type: 'button',
          text: {
            type: 'plain_text',
            text: `${PRIORITY_LEVELS.LOW.emoji} Low`
          },
          action_id: 'priority_low'
        }
      ]
    }
  ];
}

// Listen to all messages in channels where the bot is added
app.message(async ({ message, client, logger }) => {
  try {
    // Skip bot messages and message subtypes we don't care about
    if (message.subtype || message.bot_id) {
      return;
    }

    const text = message.text || '';
    const priority = detectPriority(text);

    if (priority) {
      // Add priority reaction to the message
      await addPriorityReaction(client, message.channel, message.ts, priority);
      
      logger.info(`Auto-detected ${priority} priority for message: "${text.substring(0, 50)}..."`);
    }
  } catch (error) {
    logger.error('Error processing message:', error);
  }
});

// Slash command to manually prioritize a message
app.command('/prioritize', async ({ command, ack, respond, client }) => {
  await ack();

  try {
    await respond({
      text: 'Use the buttons below to set the priority of your last message:',
      blocks: createPriorityButtons(),
      response_type: 'ephemeral'
    });
  } catch (error) {
    console.error('Error responding to /prioritize command:', error);
  }
});

// Slash command to show priority keywords
app.command('/priority-keywords', async ({ command, ack, respond }) => {
  await ack();

  const keywordsList = Object.entries(PRIORITY_KEYWORDS)
    .map(([level, keywords]) => {
      const emoji = PRIORITY_LEVELS[level].emoji;
      return `${emoji} *${level}*: ${keywords.join(', ')}`;
    })
    .join('\n');

  await respond({
    text: `*Priority Detection Keywords:*\n\n${keywordsList}\n\n_Messages containing these keywords will be automatically tagged with the corresponding priority level._`,
    response_type: 'ephemeral'
  });
});

// Handle priority button clicks
['critical', 'high', 'medium', 'low'].forEach(priority => {
  app.action(`priority_${priority}`, async ({ body, ack, client, respond }) => {
    await ack();

    try {
      const priorityLevel = priority.toUpperCase();
      const priorityInfo = PRIORITY_LEVELS[priorityLevel];
      
      // Get the channel history to find the user's last message
      const result = await client.conversations.history({
        channel: body.channel.id,
        limit: 10
      });

      // Find the most recent message from the user (not from bot)
      const userMessage = result.messages.find(msg => 
        msg.user === body.user.id && !msg.bot_id && msg.text
      );

      if (userMessage) {
        // Add priority reaction to the user's message
        await addPriorityReaction(client, body.channel.id, userMessage.ts, priorityLevel);
        
        await respond({
          text: `${priorityInfo.emoji} Message prioritized as *${priorityInfo.name}*!`,
          response_type: 'ephemeral',
          replace_original: true
        });
      } else {
        await respond({
          text: '❌ Could not find a recent message to prioritize. Please send a message first.',
          response_type: 'ephemeral',
          replace_original: true
        });
      }
    } catch (error) {
      console.error(`Error handling priority_${priority} action:`, error);
      await respond({
        text: '❌ An error occurred while setting the priority.',
        response_type: 'ephemeral',
        replace_original: true
      });
    }
  });
});

// App home tab - shows user info and priority stats
app.event('app_home_opened', async ({ event, client, logger }) => {
  try {
    await client.views.publish({
      user_id: event.user,
      view: {
        type: 'home',
        blocks: [
          {
            type: 'header',
            text: {
              type: 'plain_text',
              text: '📊 Message Priority Dashboard'
            }
          },
          {
            type: 'section',
            text: {
              type: 'mrkdwn',
              text: '*Welcome to the Slack Message Prioritization App!*\n\nThis app helps you manage and prioritize your messages effectively.'
            }
          },
          {
            type: 'divider'
          },
          {
            type: 'section',
            text: {
              type: 'mrkdwn',
              text: '*How it works:*\n\n• 🤖 *Automatic Detection*: Messages with priority keywords are automatically tagged\n• 🔘 *Manual Tagging*: Use `/prioritize` to manually set message priority\n• 📝 *View Keywords*: Use `/priority-keywords` to see the priority detection keywords\n• 🎨 *Visual Indicators*: Priority levels are shown with colored emoji reactions'
            }
          },
          {
            type: 'divider'
          },
          {
            type: 'section',
            text: {
              type: 'mrkdwn',
              text: `*Priority Levels:*\n\n${PRIORITY_LEVELS.CRITICAL.emoji} *Critical* - Urgent issues requiring immediate attention\n${PRIORITY_LEVELS.HIGH.emoji} *High* - Important tasks with deadlines\n${PRIORITY_LEVELS.MEDIUM.emoji} *Medium* - Standard priority items\n${PRIORITY_LEVELS.LOW.emoji} *Low* - Informational updates and FYIs`
            }
          },
          {
            type: 'divider'
          },
          {
            type: 'section',
            text: {
              type: 'mrkdwn',
              text: '*Commands:*\n\n`/prioritize` - Manually prioritize your last message\n`/priority-keywords` - View priority detection keywords'
            }
          }
        ]
      }
    });
  } catch (error) {
    logger.error('Error publishing app home:', error);
  }
});

// Start the app
(async () => {
  try {
    await app.start();
    console.log('⚡️ Slack Messaging Prioritization App is running!');
    console.log(`🎯 Priority Keywords Loaded:`);
    Object.entries(PRIORITY_KEYWORDS).forEach(([level, keywords]) => {
      console.log(`   ${PRIORITY_LEVELS[level].emoji} ${level}: ${keywords.join(', ')}`);
    });
  } catch (error) {
    console.error('Failed to start app:', error);
    process.exit(1);
  }
})();

// Handle graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n🛑 Shutting down gracefully...');
  await app.stop();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\n🛑 Shutting down gracefully...');
  await app.stop();
  process.exit(0);
});
