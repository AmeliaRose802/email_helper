import React, { useEffect, useState } from 'react';
import '@/styles/task-celebration.css';

interface TaskCelebrationProps {
  onComplete?: () => void;
}

const EMOJIS = ['🎉', '✨', '🌟', '⭐', '💫', '🎊', '🎈', '🏆', '👏', '🙌'];
const PARTICLE_COUNT = 20;

interface Particle {
  id: number;
  emoji: string;
  x: number;
  y: number;
  rotation: number;
  scale: number;
  delay: number;
}

export const TaskCelebration: React.FC<TaskCelebrationProps> = ({ onComplete }) => {
  const [particles, setParticles] = useState<Particle[]>([]);

  useEffect(() => {
    // Generate random particles
    const newParticles: Particle[] = Array.from({ length: PARTICLE_COUNT }, (_, i) => ({
      id: i,
      emoji: EMOJIS[Math.floor(Math.random() * EMOJIS.length)],
      x: Math.random() * 100 - 50, // -50 to 50
      y: Math.random() * 100 - 50, // -50 to 50
      rotation: Math.random() * 720 - 360, // -360 to 360 degrees
      scale: Math.random() * 0.5 + 0.5, // 0.5 to 1
      delay: Math.random() * 0.2, // 0 to 0.2s delay
    }));
    setParticles(newParticles);

    // Auto-complete after animation duration
    const timer = setTimeout(() => {
      if (onComplete) {
        onComplete();
      }
    }, 1500); // Animation duration

    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <div className="task-celebration">
      <div className="celebration-container">
        {particles.map((particle) => (
          <div
            key={particle.id}
            className="celebration-particle"
            style={{
              '--particle-x': `${particle.x}vw`,
              '--particle-y': `${particle.y}vh`,
              '--particle-rotation': `${particle.rotation}deg`,
              '--particle-scale': particle.scale,
              '--particle-delay': `${particle.delay}s`,
            } as React.CSSProperties}
          >
            {particle.emoji}
          </div>
        ))}
      </div>
      <div className="celebration-message">
        <span className="celebration-text">🎉 Task Complete! 🎉</span>
      </div>
    </div>
  );
};
