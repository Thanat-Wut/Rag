import CountUp from '../magic/CountUp';
import FadeInUp from '../magic/FadeInUp';

export default function Page4_Results() {
  return (
    <div className="bg-slate-900 text-white w-full h-full flex flex-col items-center justify-center p-8 text-center">
      <FadeInUp>
        <h2 className="text-4xl md:text-6xl font-bold mb-16">System Impact</h2>
      </FadeInUp>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-12 w-full max-w-4xl mb-20">
        <StatItem value={60} suffix="%" label="Reduction in Ticket Volume" delay={0.2} />
        <StatItem value={24} suffix="/7" label="Availability" delay={0.4} />
        <StatItem value={2} suffix="s" label="Average Response Time" delay={0.6} />
      </div>

      <FadeInUp delay={0.8}>
        <div className="bg-slate-800/50 px-8 py-4 rounded-full border border-slate-700 inline-flex items-center gap-4">
          <span className="text-slate-400">Powered by</span>
          <span className="font-bold text-orange-400">FastAPI</span>
          <span className="font-bold text-blue-400">React</span>
          <span className="font-bold text-teal-400">Tailwind</span>
          <span className="font-bold text-purple-400">Framer Motion</span>
        </div>
      </FadeInUp>
    </div>
  );
}

function StatItem({ value, suffix, label, delay }: any) {
  return (
    <div className="flex flex-col items-center">
      <div className="text-6xl md:text-8xl font-bold text-mango-500 mb-2">
        <CountUp end={value} suffix={suffix} duration={2.5} />
      </div>
      <p className="text-xl text-slate-400 font-light">{label}</p>
    </div>
  );
}