import React, { useState, useEffect } from 'react';

// Demo data for tickets and analysis
const mockTickets = [
  { key: 'CPE-3117', summary: 'Address customer login failures' },
  { key: 'CPE-2048', summary: 'Improve dashboard performance' },
];

const mockAnalysis = {
  topPriority: 'CPE-3117',
  reasoning:
    `Your top priority should be CPE-3117 because it is blocking several customer sign-ins.`,
  urgency:
    `This ticket affects customers directly and has been open for several days without progress.`,
  nextSteps: [
    'Review recent authentication logs',
    'Reproduce the login issue locally',
    'Prepare a hotfix and communicate status',
  ],
  howICanHelp: [
    'Research similar incidents',
    'Draft a status update comment',
  ],
  otherNotable: [
    { key: 'CPE-2048', note: 'Performance complaints increasing from users' },
  ],
};

export default function PersonalTicketAssistant() {
  const [isDemoMode, setIsDemoMode] = useState(true);
  const [loading, setLoading] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [tickets, setTickets] = useState(mockTickets);
  const [aiAnalysis, setAiAnalysis] = useState(mockAnalysis);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [view, setView] = useState('analysis');

  useEffect(() => {
    if (!isDemoMode) {
      fetchRealData();
    }
  }, [isDemoMode]);

  const fetchRealData = async () => {
    setLoading(true);
    setAnalysisLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/session/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        const data = await response.json();
        setTickets(data.tickets || []);

        if (data.analysis) {
          setAiAnalysis({
            topPriority: data.analysis.top_priority?.key || null,
            reasoning: data.analysis.priority_reasoning || '',
            urgency: data.analysis.summary || '',
            nextSteps: data.analysis.next_steps || [],
            howICanHelp: data.analysis.can_help_with || [],
            otherNotable:
              data.analysis.other_notable?.slice(0, 2).map((t) => ({
                key: t.key,
                note: t.summary,
              })) || [],
          });
        }
      }
    } catch (error) {
      console.error('Error fetching real data:', error);
      setTickets(mockTickets);
      setAiAnalysis(mockAnalysis);
    } finally {
      setLoading(false);
      setAnalysisLoading(false);
    }
  };

  const toggleDemoMode = () => {
    setIsDemoMode(!isDemoMode);
    if (isDemoMode) {
      fetchRealData();
    } else {
      setTickets(mockTickets);
      setAiAnalysis(mockAnalysis);
    }
  };

  const AnalysisView = () => {
    const currentTickets = tickets;
    const topPriorityKey =
      typeof aiAnalysis?.topPriority === 'string'
        ? aiAnalysis.topPriority
        : aiAnalysis?.topPriority?.key;

    const focusTicket = currentTickets.find(
      (t) => t.key === (selectedTicket || topPriorityKey)
    );

    if (analysisLoading) {
      return (
        <div className="max-w-4xl mx-auto text-center py-8">
          <div className="w-8 h-8 border-2 border-slate-600 border-t-slate-400 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Analyzing your tickets with AI...</p>
        </div>
      );
    }

    if (!aiAnalysis) {
      return (
        <div className="max-w-4xl mx-auto text-center py-8">
          <p className="text-slate-400">
            No analysis available. Switch to Live Mode to get AI insights.
          </p>
        </div>
      );
    }

    return (
      <div className="analysis-view">
        <h2>Top Priority: {focusTicket?.key}</h2>
        <p>{aiAnalysis.reasoning}</p>
        <p>{aiAnalysis.urgency}</p>
        <h3>Next Steps</h3>
        <ul>
          {aiAnalysis.nextSteps.map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ul>
        <h3>How I Can Help</h3>
        <ul>
          {aiAnalysis.howICanHelp.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
        <h3>Other Notable Tickets</h3>
        <ul>
          {aiAnalysis.otherNotable.map((t) => (
            <li key={t.key}>
              {t.key}: {t.note}
            </li>
          ))}
        </ul>
      </div>
    );
  };

  const WorkView = () => {
    const currentTickets = tickets;
    const topPriorityKey =
      typeof aiAnalysis?.topPriority === 'string'
        ? aiAnalysis.topPriority
        : aiAnalysis?.topPriority?.key;

    const focusTicket = currentTickets.find(
      (t) => t.key === (selectedTicket || topPriorityKey)
    );

    if (!aiAnalysis || analysisLoading) {
      return <div>Loading work analysis...</div>;
    }

    const workSteps = aiAnalysis.nextSteps || [];
    const helpItems = aiAnalysis.howICanHelp || [];

    return (
      <div className="work-view">
        <h2>Working on {focusTicket?.key}</h2>
        <h3>Next Steps</h3>
        <ul>
          {workSteps.map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ul>
        <h3>How I Can Help</h3>
        <ul>
          {helpItems.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div>
      <button onClick={toggleDemoMode}>
        {isDemoMode ? 'Switch to Live Mode' : 'Switch to Demo Mode'}
      </button>
      {view === 'analysis' ? <AnalysisView /> : <WorkView />}
    </div>
  );
}

