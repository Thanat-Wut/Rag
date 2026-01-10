import { useState, useRef, useEffect } from 'react';
import Page1_Problem from './pages/Page1_Problem';
import Page2_Solution from './pages/Page2_Solution';
import Page3_Demo from './pages/Page3_Demo';
import Page4_Results from './pages/Page4_Results';
import NavDots from './components/NavDots';

function App() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // ตรวจจับการเลื่อนหน้า
  const handleScroll = () => {
    if (containerRef.current) {
      const index = Math.round(
        containerRef.current.scrollTop / window.innerHeight
      );
      setCurrentSlide(index);
    }
  };

  // กดจุดแล้วเลื่อนไปหน้านั้น
  const scrollToSlide = (index: number) => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: index * window.innerHeight,
        behavior: 'smooth'
      });
    }
  };

  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, []);

  return (
    <>
      <NavDots 
        currentSlide={currentSlide} 
        totalSlides={4} 
        onDotClick={scrollToSlide} 
      />
      
      <main ref={containerRef} className="snap-container">
        <section className="snap-slide"><Page1_Problem /></section>
        <section className="snap-slide"><Page2_Solution /></section>
        <section className="snap-slide"><Page3_Demo /></section>
        <section className="snap-slide"><Page4_Results /></section>
      </main>
    </>
  );
}

export default App;