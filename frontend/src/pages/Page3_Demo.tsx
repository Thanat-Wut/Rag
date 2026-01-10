import { useState } from 'react';
import { helpdeskAPI, HelpdeskResponse } from '../api/helpdesk';
import ConfidenceBadge from '../components/ConfidenceBadge';
import { motion, AnimatePresence } from 'framer-motion';

export default function Page3_Demo() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<HelpdeskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      // เรียก API จริง
      const res = await helpdeskAPI.query({ query });
      setResult(res);
    } catch (err) {
      setError('Connection failed. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-50 w-full h-full flex flex-col md:flex-row p-4 md:p-8 gap-6 justify-center items-center">
      
      {/* Left: Input Area */}
      <div className="w-full md:w-1/3 flex flex-col gap-6">
        <div>
          <h2 className="text-3xl font-bold text-slate-900 mb-2">Live Demo 🚀</h2>
          <p className="text-slate-500">พิมพ์คำถามเพื่อทดสอบ AI Orchestrator</p>
        </div>

        <form onSubmit={handleAsk} className="relative">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="เช่น ขอเบิกค่าเดินทาง, เน็ตใช้ไม่ได้..."
            className="w-full h-32 p-4 rounded-xl border-2 border-slate-200 focus:border-orange-500 focus:ring-0 resize-none text-lg shadow-sm"
          />
          <button
            type="submit"
            disabled={loading}
            className="absolute bottom-4 right-4 bg-mango-500 hover:bg-mango-600 text-white px-6 py-2 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Thinking...' : 'Ask AI'}
          </button>
        </form>

        {/* Suggestion Chips */}
        <div className="flex flex-wrap gap-2">
          {['ขอเบิกค่าเดินทาง', 'Internet เข้าไม่ได้', 'ขอลาป่วยต้องทำไง', 'สวัสดีครับ'].map(q => (
            <button key={q} onClick={() => setQuery(q)} className="text-xs bg-white border border-slate-200 px-3 py-1 rounded-full hover:border-orange-400 text-slate-600">
              {q}
            </button>
          ))}
        </div>
        
        {error && <div className="text-red-500 bg-red-50 p-3 rounded-lg text-sm">{error}</div>}
      </div>

      {/* Right: Result Area */}
      <div className="w-full md:w-1/2 h-[500px] bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden relative flex flex-col">
        <div className="bg-slate-900 text-white p-4 flex justify-between items-center">
          <span className="font-mono text-sm">AI Orchestrator Response</span>
          {result && <span className="text-xs bg-slate-800 px-2 py-1 rounded text-green-400">Trace: {result.trace_id.slice(0,8)}</span>}
        </div>

        <div className="flex-1 p-6 overflow-y-auto bg-slate-50/50">
          <AnimatePresence mode="wait">
            {!result && !loading && (
              <div className="h-full flex items-center justify-center text-slate-400">
                Waiting for input...
              </div>
            )}
            
            {loading && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full flex flex-col items-center justify-center gap-4">
                <div className="w-8 h-8 border-4 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-slate-500 animate-pulse">Analyzing intent...</p>
              </motion.div>
            )}

            {result && (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                {/* Header Info */}
                <div className="flex items-center gap-3 mb-4">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${result.action === 'answer' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                    {result.action}
                  </span>
                  <ConfidenceBadge confidence={result.confidence} />
                  <span className="text-xs text-slate-400 ml-auto">{result.processing_time_ms.toFixed(0)}ms</span>
                </div>

                {/* Main Content */}
                {result.action === 'answer' ? (
                  <div className="bg-white p-6 rounded-xl border border-green-100 shadow-sm">
                    <h3 className="text-slate-500 text-sm mb-2 font-bold">AI ANSWER:</h3>
                    <p className="text-lg text-slate-800 leading-relaxed">{result.answer}</p>
                  </div>
                ) : (
                  <div className="bg-white p-0 rounded-xl border border-blue-100 shadow-sm overflow-hidden">
                    <div className="bg-blue-50/50 p-4 border-b border-blue-100">
                      <h3 className="text-blue-700 font-bold flex items-center gap-2">
                        <span>🎫</span> Creating Ticket
                      </h3>
                    </div>
                    <div className="p-5 space-y-3">
                      <div>
                        <div className="text-xs text-slate-400 uppercase">Subject</div>
                        <div className="font-medium">{result.ticket?.subject}</div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="text-xs text-slate-400 uppercase">Department</div>
                          <div className="font-medium text-slate-900">{result.ticket?.department}</div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-400 uppercase">Priority</div>
                          <div className={`inline-flex px-2 rounded text-xs font-bold uppercase ${result.ticket?.priority === 'high' ? 'bg-red-100 text-red-600' : 'bg-slate-100 text-slate-600'}`}>
                            {result.ticket?.priority}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Debug Info */}
                <div className="text-xs text-slate-300 font-mono mt-8 border-t pt-4">
                  Query intent: {result.ticket?.department || 'General'}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}