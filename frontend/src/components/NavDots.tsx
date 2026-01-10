import { motion } from 'framer-motion';

interface NavDotsProps {
  currentSlide: number;
  totalSlides: number;
  onDotClick: (index: number) => void;
}

export default function NavDots({ 
  currentSlide, 
  totalSlides, 
  onDotClick 
}: NavDotsProps) {
  return (
    <div className="nav-dots">
      {Array.from({ length: totalSlides }).map((_, index) => (
        <motion.button
          key={index}
          className={`dot ${currentSlide === index ? 'active' : ''}`}
          onClick={() => onDotClick(index)}
          whileHover={{ scale: 1.2 }}
          whileTap={{ scale: 0.9 }}
          aria-label={`Go to slide ${index + 1}`}
        />
      ))}
    </div>
  );
}