import React, { useState, useMemo } from 'react';
import {
  ChevronRight,
  AlertTriangle,
  Clock,
  User,
  Calendar,
  Search,
  Target,
  Brain,
  ArrowRight,
  CheckCircle,
  Play
} from 'lucide-react';

const PersonalTicketAssistant = () => {
  const [currentView, setCurrentView] = useState('tickets'); // tickets, analysis, work
  const [selectedTicket, setSelectedTicket] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Real ticket data from your CLI output
  const allTickets = [
    { key: 'CPE-3313', priority: 'P1', status: 'In Progress', age: '99d', stale: '21d', summary: '[PRD] Update Mac Netskope Client to v126' },
    { key: 'VMR-320', priority: 'P1', status: 'To Do', age: '1482d', stale: '1470d', summary: 'GOTS-Critical-152190: Google Chrome < 92.0.4515.131 Multiple Vulnerabilities' },
    { key: 'CPE-3360', priority: 'P2', status: 'In Progress', age: '64d', stale: '23d', summary: 'Cortex Discovery: Endpoints in the list attached ore on the older version OS' },
    { key: 'CPE-3470', priority: 'P3', status: 'To Do', age: '0d', stale: '0d', summary: 'macOS Zscaler Agent Installation' },
    { key: 'CPE-3461', priority: 'P3', status: 'To Do', age: '6d', stale: '6d', summary: 'Self-Heal policies must achieve 100% success' },
    { key: 'CPE-3395', priority: 'P3', status: 'To Do', age: '28d', stale: '7d', summary: 'CLONE - DTS Endpoints - 179692 - Node.js 16.x < 16.20.2 / 18.x < 18.17.1 / 20.x' },
    { key: 'CPE-3433', priority: 'P3', status: 'In Progress', age: '15d', stale: '13d', summary: 'decommissioning Miro Desktop from Self Service ( Mac )' },
    { key: 'CPE-3412', priority: 'P3', status: 'In Progress', age: '27d', stale: '15d', summary: 'CLONE - DTS Endpoints - 234350 - pgAdmin < 9.2 Multiple Vulnerabilities' },
    { key: 'CPE-3385', priority: 'P3', status: 'Backlog', age: '36d', stale: '36d', summary: 'thick app updates on MacOS' },
    { key: 'CPE-3357', priority: 'P3', status: 'To Do', age: '65d', stale: '44d', summary: 'jamf self service+ testing and deployment' },
    { key: 'CPE-3284', priority: 'P3', status: 'To Do', age: '118d', stale: '44d', summary: 'Implement Automated Change Log System for CPE Team Deployments' },
    { key: 'CPE-3375', priority: 'P3', status: 'Backlog', age: '48d', stale: '44d', summary: 'TLS version to 1.3 for SSL Configurations jamf.docusignhq.com:443' },
    { key: 'CPE-3359', priority: 'P3', status: 'To Do', age: '65d', stale: '51d', summary: 'prep deployment package for self service +' },
    { key: 'CPE-3358', priority: 'P3', status: 'To Do', age: '65d', stale: '51d', summary: 'test self service+ in sandbox' },
    { key: 'CPE-3337', priority: 'P3', status: 'To Do', age: '90d', stale: '58d', summary: 'Security Features' },
    { key: 'CPE-3219', priority: 'P3', status: 'To Do', age: '153d', stale: '68d', summary: 'Gather Jamf Enrollment failures for March' },
    { key: 'CPE-3334', priority: 'P3', status: 'In Progress', age: '90d', stale: '77d', summary: 'Mac IT Support AI Platform' },
    { key: 'CPE-3206', priority: 'P3', status: 'To Do', age: '162d', stale: '79d', summary: 'Develop API script to verify asset lock for terminated employee devices' },
    { key: 'CPE-3091', priority: 'P3', status: 'Waiting', age: '219d', stale: '91d', summary: 'Implement Scheduled Restarts for macOS System Updates' },
    { key: 'CPE-3321', priority: 'P3', status: 'To Do', age: '93d', stale: '93d', summary: 'Update Cortex XDR self-service packages to 8.8 version' },
    { key: 'CPE-2881', priority: 'P3', status: 'To Do', age: '351d', stale: '96d', summary: 'Datadog POC for picking binary JFrog Artifactory' },
    { key: 'CPE-3311', priority: 'P3', status: 'To Do', age: '99d', stale: '99d', summary: 'Internet "Sharing" Greyed Out MacOS 15.5' },
    { key: 'CPE-3117', priority: 'P3', status: 'To Do', age: '209d', stale: '105d', summary: 'Failure - Auto lock macs via snow integration' },
    { key: 'CPE-3226', priority: 'P3', status: 'To Do', age: '149d', stale: '149d', summary: 'Phase 1: Secure BYOD Rollout' },
    { key: 'CPE-3222', priority: 'P3', status: 'To Do', age: '153d', stale: '153d', summary: 'Create a KB for Jamf log collection of failed enrolment' },
    { key: 'CPE-3008', priority: 'P3', status: 'To Do', age: '273d', stale: '166d', summary: 'Uptime notifications' },
    { key: 'CPE-3108', priority: 'P3', status: 'To Do', age: '216d', stale: '167d', summary: 'Build process to detect outlier license consumption' },
    { key: 'CPE-2925', priority: 'P3', status: 'To Do', age: '321d', stale: '167d', summary: '[PRD] Enhancing Security and Change Management for Jamf' },
    { key: 'CPE-2866', priority: 'P3', status: 'To Do', age: '355d', stale: '167d', summary: 'Develop a policy on which computers should be locked' },
    { key: 'CPE-3179', priority: 'P3', status: 'To Do', age: '175d', stale: '167d', summary: 'Create instructions for IT to use the script' },
    { key: 'CPE-3118', priority: 'P3', status: 'To Do', age: '209d', stale: '168d', summary: 'Make LAPS Passwords for GCS Admin Easier for Technicians' },
    { key: 'CPE-2458', priority: 'P3', status: 'To Do', age: '579d', stale: '307d', summary: 'Complete Jamf security & architecture review' },
    { key: 'EUSOPS-180', priority: 'P3', status: 'Backlog', age: '595d', stale: '418d', summary: 'Review Enrolled Vendors to ABM' }
  ];

  // AI Analysis data (from your CLI output)
  const aiAnalysis = {
    topPriority: 'CPE-3117',
    reasoning: `Your top priority should be CPE-3117 Failure - Auto lock macs via snow integration, labeled as VOC_Feedback. This ticket has a significant customer impact, and the issue is causing devices to fail auto-locking. The current process for managing scripts within Jamf lacks robust security measures and change tracking, which poses risks for unauthorized modifications and potential vulnerabilities.`,
    urgency: `This ticket affects customers directly, as they're experiencing failed auto-locking on their Macs. It's a critical issue that requires immediate attention to prevent data loss or other consequences.`,
    nextSteps: [
      'Reach out to the snow integration team to investigate the cause of the failure',
      'Review the Jamf script logs to identify any errors or inconsistencies',
      'Develop a plan to implement additional security measures and change tracking for scripts in Jamf'
    ],
    howICanHelp: [
      'Researching the cause of the snow integration failure',
      'Reviewing the Jamf script logs with you',
      'Developing a solution plan with you'
    ],
    otherNotable: [
      { key: 'CPE-3118', note: 'Make LAPS Passwords for GCS Admin Easier for Technicians: This ticket is related to improving the ease of use for technicians when retrieving and entering the LAPS password.' },
      { key: 'CPE-2925', note: "PRD - Enhancing Security and Change Management for Jamf: This epic review is essential for ensuring Jamf's security measures are robust enough to prevent issues like the one we're currently addressing." }
    ]
  };

  const filteredTickets = useMemo(() => {
    if (!searchQuery) return allTickets;
    return allTickets.filter(t =>
      t.key.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.summary.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [searchQuery, allTickets]);

  const getPriorityColor = (priority) => {
    switch(priority) {
      case 'P1': return 'text-red-400';
      case 'P2': return 'text-amber-400';
      default: return 'text-blue-400';
    }
  };

  const getPriorityBg = (priority) => {
    switch(priority) {
      case 'P1': return 'bg-red-500/10 border-red-500/30';
      case 'P2': return 'bg-amber-500/10 border-amber-500/30';
      default: return 'bg-blue-500/10 border-blue-500/30';
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'In Progress': return 'text-green-400';
      case 'Waiting': return 'text-amber-400';
      case 'Backlog': return 'text-slate-500';
      default: return 'text-slate-300';
    }
  };

  const TicketsView = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Your Tickets</h1>
          <p className="text-slate-400">{filteredTickets.length} tickets in your queue</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setCurrentView('analysis')}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-purple-800 transition-all"
          >
            <Brain className="w-4 h-4" />
            AI Priority Analysis
          </button>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          placeholder="Search tickets..."
          className="w-full pl-10 pr-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-lg text-slate-300 placeholder-slate-500"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden">
        <div className="grid grid-cols-12 gap-4 p-4 border-b border-slate-700/50 text-slate-400 text-sm font-semibold">
          <div className="col-span-2">Key</div>
          <div className="col-span-1">Priority</div>
          <div className="col-span-2">Status</div>
          <div className="col-span-1">Age</div>
          <div className="col-span-1">Stale</div>
          <div className="col-span-5">Summary</div>
        </div>
        
        <div className="divide-y divide-slate-700/30">
          {filteredTickets.map(ticket => (
            <div
              key={ticket.key}
              className={`grid grid-cols-12 gap-4 p-4 hover:bg-slate-700/20 transition-colors cursor-pointer ${
                ticket.key === aiAnalysis.topPriority ? 'bg-purple-500/5 border-l-4 border-purple-500' : ''
              }`}
              onClick={() => {
                setSelectedTicket(ticket.key);
                setCurrentView('analysis');
              }}
            >
              <div className="col-span-2 font-mono text-slate-300">{ticket.key}</div>
              <div className={`col-span-1 font-semibold ${getPriorityColor(ticket.priority)}`}>{ticket.priority}</div>
              <div className={`col-span-2 ${getStatusColor(ticket.status)}`}>{ticket.status}</div>
              <div className="col-span-1 text-slate-400">{ticket.age}</div>
              <div className="col-span-1 text-slate-400">{ticket.stale}</div>
              <div className="col-span-5 text-slate-300 truncate">{ticket.summary}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="text-center">
        <p className="text-slate-500 text-sm">
          Click on any ticket or use <strong>AI Priority Analysis</strong> to get focused guidance
        </p>
      </div>
    </div>
  );

  const AnalysisView = () => {
    const focusTicket = allTickets.find(t => t.key === (selectedTicket || aiAnalysis.topPriority));

    return (
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setCurrentView('tickets')}
            className="flex items-center gap-2 text-slate-400 hover:text-slate-300"
          >
            <ChevronRight className="w-4 h-4 rotate-180" />
            Back to tickets
          </button>
        </div>

        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-100 mb-2">AI Work Analysis</h1>
          <p className="text-slate-400">Based on customer impact, urgency, and your expertise</p>
        </div>

        <div className="bg-gradient-to-r from-purple-500/10 to-cyan-500/10 border-2 border-purple-500/30 rounded-xl p-8">
          <div className="flex items-start gap-4 mb-6">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-red-500/20 border border-red-500/30 rounded-xl flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-400" />
              </div>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <span className={`px-3 py-1 rounded-lg text-sm border font-semibold ${getPriorityBg(focusTicket?.priority)}`}>
                  TOP PRIORITY
                </span>
                <span className="text-slate-400">•</span>
                <span className="text-slate-300">{focusTicket?.key}</span>
              </div>
              <h2 className="text-xl font-bold text-slate-100 mb-2">{focusTicket?.summary}</h2>
              <div className="flex items-center gap-4 text-sm text-slate-400">
                <span>Priority: {focusTicket?.priority}</span>
                <span>Status: {focusTicket?.status}</span>
                <span>Age: {focusTicket?.age}</span>
                <span>Labels: VOC_Feedback</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-6">
            <h3 className="font-semibold text-slate-200 mb-3">Why it's urgent:</h3>
            <p className="text-slate-300 mb-4">{aiAnalysis.urgency}</p>

            <h3 className="font-semibold text-slate-200 mb-3">Next concrete steps:</h3>
            <ol className="list-decimal list-inside space-y-2 text-slate-300 mb-4">
              {aiAnalysis.nextSteps.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
          </div>

          <div className="flex gap-4 mt-6">
            <button
              onClick={() => setCurrentView('work')}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-purple-800 transition-all flex items-center justify-center gap-2"
            >
              <Play className="w-4 h-4" />
              Let's work on this
            </button>
            <button
              onClick={() => setCurrentView('tickets')}
              className="px-6 py-3 bg-slate-700/50 hover:bg-slate-600/50 border border-slate-600/30 rounded-lg text-slate-200 transition-colors"
            >
              Pick different ticket
            </button>
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
          <h3 className="font-semibold text-slate-200 mb-4">How I can help</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {aiAnalysis.howICanHelp.map((help, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-slate-700/30 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                <span className="text-slate-300">{help}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
          <h3 className="font-semibold text-slate-200 mb-4">Other notable tickets</h3>
          <div className="space-y-3">
            {aiAnalysis.otherNotable.map(item => (
              <div key={item.key} className="border-l-4 border-slate-600 pl-4">
                <div className="font-semibold text-slate-300 mb-1">{item.key}</div>
                <div className="text-slate-400 text-sm">{item.note}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const WorkView = () => {
    const focusTicket = allTickets.find(t => t.key === (selectedTicket || aiAnalysis.topPriority));

    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setCurrentView('analysis')}
              className="flex items-center gap-2 text-slate-400 hover:text-slate-300"
            >
              <ChevronRight className="w-4 h-4 rotate-180" />
              Back to analysis
            </button>
            <div className="h-6 w-px bg-slate-700"></div>
            <div>
              <h1 className="text-xl font-bold text-slate-100">Working on {focusTicket?.key}</h1>
              <p className="text-slate-400 text-sm">{focusTicket?.summary}</p>
            </div>
          </div>
        </div>

        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
          <p className="text-amber-200">
            <strong>Starting point:</strong> This is where you'd see the guided workflow for actually working on the ticket.
            The analysis told you WHAT to do, now we help you DO it step by step.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
              <h3 className="font-semibold text-slate-200 mb-4">First, let's understand the problem</h3>
              <div className="space-y-3">
                <div className="p-3 bg-slate-700/30 rounded-lg">
                  <div className="font-semibold text-slate-300">What we know:</div>
                  <div className="text-slate-400 text-sm mt-1">
                    ServiceNow integration is failing to auto-lock Mac devices. Customer-reported issue with security implications.
                  </div>
                </div>
                <div className="p-3 bg-slate-700/30 rounded-lg">
                  <div className="font-semibold text-slate-300">What we need to find out:</div>
                  <div className="text-slate-400 text-sm mt-1">
                    Error patterns in logs, API connectivity status, affected device segments
                  </div>
                </div>
              </div>

              <button className="w-full mt-4 px-4 py-2 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-600/30 text-purple-300 rounded-lg transition-colors">
                Start investigation
              </button>
            </div>
          </div>

          <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
            <h3 className="font-semibold text-slate-200 mb-4">Session Progress</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 border-2 border-slate-600 rounded-full"></div>
                <span className="text-slate-400">Problem analysis</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 border-2 border-slate-600 rounded-full"></div>
                <span className="text-slate-400">Log investigation</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 border-2 border-slate-600 rounded-full"></div>
                <span className="text-slate-400">Fix implementation</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 border-2 border-slate-600 rounded-full"></div>
                <span className="text-slate-400">Testing & validation</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-lg flex items-center justify-center">
              <Target className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-slate-100">Personal Ticket Assistant</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 bg-purple-600/20 text-purple-300 rounded-lg text-sm border border-purple-600/30">
              Beta
            </span>
            <div className="text-slate-400 text-sm">
              {new Date().toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </div>
          </div>
        </div>
      </header>

      <main className="p-6">
        {currentView === 'tickets' && <TicketsView />}
        {currentView === 'analysis' && <AnalysisView />}
        {currentView === 'work' && <WorkView />}
      </main>
    </div>
  );
};

export default PersonalTicketAssistant;
