import FadeInUp from '../magic/FadeInUp';
import StaggerContainer, { StaggerItem } from '../magic/StaggerContainer';

export default function Page1_Problem() {
  const problems = [
    { icon: "😫", title: "Information Overload", desc: "พนักงานเสียเวลาหาข้อมูลใน Document เป็นชั่วโมง" },
    { icon: "🐢", title: "Slow Response", desc: "HR และ IT ตอบคำถามซ้ำๆ จนไม่มีเวลาทำงานหลัก" },
    { icon: "📉", title: "Inefficient Process", desc: "การส่งต่อเรื่องผิดแผนก ทำให้การแก้ปัญหาล่าช้า" }
  ];

  return (
    <div className="bg-slate-900 text-white w-full h-full flex flex-col items-center justify-center p-8">
      <FadeInUp>
        <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-orange-400 to-red-500 text-transparent bg-clip-text">
          The Challenge
        </h1>
        <p className="text-xl md:text-2xl text-slate-300 mb-16 text-center max-w-2xl">
          ทำไมการขอความช่วยเหลือภายในองค์กร ถึงเป็นเรื่องยาก?
        </p>
      </FadeInUp>

      <StaggerContainer staggerDelay={0.2}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl w-full">
          {problems.map((p, idx) => (
            <StaggerItem key={idx}>
              <div className="bg-slate-800/50 p-8 rounded-2xl border border-slate-700 hover:border-orange-500/50 transition-colors">
                <div className="text-6xl mb-4">{p.icon}</div>
                <h3 className="text-2xl font-bold mb-2 text-white">{p.title}</h3>
                <p className="text-slate-400">{p.desc}</p>
              </div>
            </StaggerItem>
          ))}
        </div>
      </StaggerContainer>
    </div>
  );
}