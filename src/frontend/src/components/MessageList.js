import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './MessageList.scss';
import botAvatar from '../assets/logo.png';

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
              {message.sender === 'bot' && (
                <img
                  src={botAvatar}
                  alt={`${message.sender} avatar`}
                  className="avatar"
                />
              )}
              <div 
                className="text"
                dangerouslySetInnerHTML={{ __html: message.text }}
              />
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default MessageList;