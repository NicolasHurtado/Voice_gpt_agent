'use client';

import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { AudioAnalyzerData } from '@/types/audio';
import { cn } from '@/utils/helpers';

interface AudioWaveformProps {
  analyzerData: AudioAnalyzerData;
  isRecording: boolean;
  className?: string;
  height?: number;
  color?: string;
  barCount?: number;
}

export function AudioWaveform({
  analyzerData,
  isRecording,
  className,
  height = 60,
  color = '#3b82f6',
  barCount = 32,
}: AudioWaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    // Clear canvas
    ctx.clearRect(0, 0, rect.width, height);

    if (!isRecording || analyzerData.frequencyData.length === 0) {
      // Draw static bars when not recording
      drawStaticBars(ctx, rect.width, height, barCount, color);
      return;
    }

    // Draw frequency data
    drawFrequencyBars(
      ctx,
      analyzerData.frequencyData,
      rect.width,
      height,
      barCount,
      color
    );
  }, [analyzerData, isRecording, height, color, barCount]);

  return (
    <motion.div
      className={cn(
        'relative overflow-hidden rounded-lg bg-gray-100',
        className
      )}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <canvas
        ref={canvasRef}
        className='w-full'
        style={{ height: `${height}px` }}
      />

      {/* Volume indicator */}
      {isRecording && (
        <motion.div
          className='absolute inset-0 pointer-events-none'
          style={{
            background: `radial-gradient(circle at center, ${color}10 0%, transparent 70%)`,
          }}
          animate={{
            opacity: analyzerData.volume * 2,
          }}
          transition={{ duration: 0.1 }}
        />
      )}
    </motion.div>
  );
}

// Draw static bars when not recording
function drawStaticBars(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  barCount: number,
  color: string
) {
  const barWidth = width / barCount;
  const barGap = barWidth * 0.2;
  const actualBarWidth = barWidth - barGap;

  ctx.fillStyle = color + '30'; // Semi-transparent

  for (let i = 0; i < barCount; i++) {
    const x = i * barWidth + barGap / 2;
    const barHeight = height * 0.3; // Static height
    const y = (height - barHeight) / 2;

    ctx.fillRect(x, y, actualBarWidth, barHeight);
  }
}

// Draw frequency bars based on audio data
function drawFrequencyBars(
  ctx: CanvasRenderingContext2D,
  frequencyData: Uint8Array,
  width: number,
  height: number,
  barCount: number,
  color: string
) {
  const barWidth = width / barCount;
  const barGap = barWidth * 0.2;
  const actualBarWidth = barWidth - barGap;

  // Sample frequency data
  const dataPerBar = Math.floor(frequencyData.length / barCount);

  for (let i = 0; i < barCount; i++) {
    // Average frequency data for this bar
    let sum = 0;
    for (let j = 0; j < dataPerBar; j++) {
      const index = i * dataPerBar + j;
      if (index < frequencyData.length) {
        sum += frequencyData[index];
      }
    }
    const average = sum / dataPerBar;

    // Calculate bar properties
    const x = i * barWidth + barGap / 2;
    const barHeight = (average / 255) * height * 0.8;
    const y = (height - barHeight) / 2;

    // Create gradient
    const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight);
    gradient.addColorStop(0, color);
    gradient.addColorStop(1, color + '60');

    ctx.fillStyle = gradient;
    ctx.fillRect(x, y, actualBarWidth, barHeight);
  }
}
