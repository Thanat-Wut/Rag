import { motion } from 'framer-motion';

interface ConfidenceBadgeProps {
  confidence: number;
  animated?: boolean;
}

export default function ConfidenceBadge({ 
  confidence, 
  animated = true 
}: ConfidenceBadgeProps) {
  const getColor = (conf: number) => {
    if (conf >= 0.8) return { bg: 'bg-green-500', text: 'text-green-50', label: 'High' };
    if (conf >= 0.5) return { bg: 'bg-yellow-500', text: 'text-yellow-50', label: 'Medium' };
    return { bg: 'bg-red-500', text: 'text-red-50', label: 'Low' };
  };

  const { bg, text, label } = getColor(confidence);
  const percentage = Math.round(confidence * 100);

  const BadgeContent = (
    <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${bg} ${text} shadow-sm`}>
      <span>{label} Confidence</span>
      <span className="opacity-80">|</span>
      <span>{percentage}%</span>
    </div>
  );

  if (!animated) return BadgeContent;

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      {BadgeContent}
    </motion.div>
  );
}