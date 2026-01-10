import { useSpring, useInView } from 'framer-motion';
import { useEffect, useRef } from 'react';

interface CountUpProps {
  end: number;
  suffix?: string;
  duration?: number;
  decimals?: number;
}

export default function CountUp({ 
  end, 
  suffix = "", 
  // duration ไม่ได้ใช้ใน Spring โดยตรง แต่ใส่ไว้เผื่อขยายผลในอนาคต
  decimals = 0 
}: CountUpProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });
  
  // ใช้ Spring เพื่อให้ตัวเลขวิ่งแบบมีฟิสิกส์ (เด้งนิดๆ ตอนจบ)
  const count = useSpring(0, {
    stiffness: 50,
    damping: 20
  });

  // 1. สั่งให้เลขเริ่มวิ่งเมื่อเลื่อนมาเจอ
  useEffect(() => {
    if (isInView) {
      count.set(end);
    }
  }, [isInView, end, count]);

  // 2. อัปเดตตัวเลขใน HTML โดยตรง (แก้ Error Object not valid)
  useEffect(() => {
    const unsubscribe = count.on("change", (latest) => {
      if (ref.current) {
        const value = decimals === 0 
          ? Math.round(latest) 
          : latest.toFixed(decimals);
        
        // ใส่ตัวเลข + suffix (เช่น %) ลงไปตรงๆ
        ref.current.textContent = `${value}${suffix}`;
      }
    });
    return () => unsubscribe();
  }, [count, decimals, suffix]);

  // Return แค่ span ว่างๆ แล้วให้ useEffect ด้านบนจัดการใส่ไส้ใน
  return <span ref={ref} />;
}