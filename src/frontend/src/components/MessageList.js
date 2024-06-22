import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './MessageList.scss';

const messageVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

const MessageList = ({ messages }) => {
  return (
    <div className="message-list">
      <AnimatePresence>
        {messages.map((message) => (
          <motion.div
            key={message.id}
            className={`message ${message.sender}`}
            initial="hidden"
            animate="visible"
            exit="hidden"
            variants={messageVariants}
            transition={{ duration: 0.3 }}
          >
            <div className="message-content">
              <img
                src={message.sender === 'bot' ? '/path/to/bot-avatar.png' : '/path/to/user-avatar.png'}
                alt={`${message.sender} avatar`}
                className="avatar"
              />
              <div className="text">{message.text}</div>
            </div>
            <div className="timestamp">{new Date().toLocaleTimeString()}</div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default MessageList;
