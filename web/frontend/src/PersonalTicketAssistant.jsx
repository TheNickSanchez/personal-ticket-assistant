import React, { useState, useMemo, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { ChevronRight, AlertTriangle, Clock, User, Calendar, Search, Target, Brain, ArrowRight, CheckCircle, Play, ExternalLink, Sparkles, RefreshCw, MessageCircle, Code } from 'lucide-react';

const PersonalTicketAssistant = () => {
  const [currentView, setCurrentView] = useState('tickets'); // tickets, analysis, work
  const [selectedTicket, setSelectedTicket] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const searchInputRef = useRef(null);
  const [isDemoMode, setIsDemoMode] = useState(() => {
    // Check localStorage for saved preference, default to false (live mode)
    const saved = localStorage.getItem('isDemoMode');
    return saved ? JSON.parse(saved) : false;
  });
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [workMode, setWorkMode] = useState('brainstorm'); // 'brainstorm' or 'script'
  const [scriptContent, setScriptContent] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  
  // Debug: Track view changes
  useEffect(() => {
    console.log('Current view changed to:', currentView);
    console.log('Current state when view changed:');
    console.log('- tickets.length:', tickets.length);
    console.log('- aiAnalysis exists:', !!aiAnalysis);
    console.log('- analysisLoading:', analysisLoading);
    console.log('- isDemoMode:', isDemoMode);
  }, [currentView]);

  // Auto-fetch data when not in demo mode
  useEffect(() => {
    console.log('Component mounted. isDemoMode:', isDemoMode);
    if (!isDemoMode && tickets.length === 0) {
      console.log('Auto-fetching real data on mount');
      fetchRealData();
    }
  }, [isDemoMode]); // Only run when isDemoMode changes
  
  // Real ticket data from your CLI output
  const mockTickets = [
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

  const mockAnalysis = {
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
      { key: 'CPE-2925', note: 'PRD - Enhancing Security and Change Management for Jamf: This epic review is essential for ensuring Jamf\'s security measures are robust enough to prevent issues like the one we\'re currently addressing.' }
    ]
  };

  // Fetch real data from API
  const fetchRealData = async () => {
    setLoading(true);
    setAnalysisLoading(true);
    try {
      console.log('Fetching real data from API...');
      const response = await fetch('http://localhost:8001/api/session/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        const data = await response.json();
        console.log('Raw API data first ticket:', data.tickets?.[0]);
        
        // Helper function to calculate days difference
        const calculateDaysDiff = (dateString) => {
          if (!dateString) return 0;
          const date = new Date(dateString);
          const now = new Date();
          const diffTime = Math.abs(now - date);
          return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        };
        
        // Transform tickets to include age and stale formatted like mock data
        const transformedTickets = (data.tickets || []).map(ticket => {
          const ageDays = calculateDaysDiff(ticket.created);
          const staleDays = calculateDaysDiff(ticket.updated);
          
          const transformedTicket = {
            key: ticket.key,
            summary: ticket.summary,
            priority: ticket.priority,
            status: ticket.status,
            age: `${ageDays}d`,
            stale: `${staleDays}d`,
            assignee: ticket.assignee,
            labels: ticket.labels || [],
            issue_type: ticket.issue_type,
            created: ticket.created,
            updated: ticket.updated
          };
          
          return transformedTicket;
        });
        
        console.log('Transformed tickets first item:', transformedTickets[0]);
        setTickets(transformedTickets);

        if (data.analysis) {
          setAiAnalysis({
            topPriority: data.analysis.top_priority?.key || null,
            reasoning: data.analysis.priority_reasoning || '',
            urgency: data.analysis.summary || '',
            nextSteps: data.analysis.next_steps || [],
            howICanHelp: data.analysis.can_help_with || [],
            otherNotable:
              data.analysis.other_notable?.slice(0, 2).map(t => ({
                key: t.key,
                note: t.summary,
              })) || [],
          });
          console.log('AI Analysis set:', data.analysis);
        }
      } else {
        console.error('API call failed:', response.status);
        setTickets(mockTickets);
        setAiAnalysis(mockAnalysis);
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
  
  // Open ticket in Jira
  const openTicketInJira = async (ticketKey, e) => {
    e.stopPropagation(); // Prevent triggering the parent onClick
    
    try {
      const response = await fetch(`http://localhost:8001/api/ticket/${ticketKey}/url`);
      if (response.ok) {
        const data = await response.json();
        window.open(data.url, '_blank');
      } else {
        console.error('Failed to get ticket URL:', response.status);
      }
    } catch (error) {
      console.error('Error fetching ticket URL:', error);
    }
  };

  // Handle help action clicks
  const handleHelpAction = (helpText) => {
    // Start a chat conversation about this help item
    setChatMessages([{
      type: 'assistant',
      content: `I can help you with: "${helpText}". What specific aspect would you like to explore?`
    }]);
    setCurrentView('work');
    setWorkMode('brainstorm');
  };

  // Handle sending chat messages
  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    const userMessage = { type: 'user', content: inputMessage };
    setChatMessages(prev => [...prev, userMessage]);
    setInputMessage('');

    // Simulate AI response (in real app, this would call your backend)
    setTimeout(() => {
      const responses = [
        "Based on the ticket context, I suggest we start by reviewing the current Snow integration configuration. Would you like me to help you draft a script to check the integration status?",
        "Let's break this down into steps. First, we should gather logs from the affected systems. I can help you create a log collection script.",
        "For this type of issue, I recommend starting with a diagnostic approach. Would you like me to generate a troubleshooting checklist?"
      ];
      
      const aiResponse = {
        type: 'assistant',
        content: responses[Math.floor(Math.random() * responses.length)]
      };
      setChatMessages(prev => [...prev, aiResponse]);
    }, 1000);
  };

  // Generate sample script
  const generateScript = () => {
    const sampleScript = `#!/bin/bash
# Auto-lock verification script for Snow integration
# Generated for ticket: ${aiAnalysis?.topPriority}

echo "Checking Snow integration status..."

# Check if Snow service is running
if pgrep -x "snow-service" > /dev/null; then
    echo "✓ Snow service is running"
else
    echo "✗ Snow service is not running"
    echo "Starting Snow service..."
    sudo systemctl start snow-service
fi

# Verify auto-lock configuration
echo "Checking auto-lock configuration..."
if [ -f "/etc/snow/autolock.conf" ]; then
    echo "✓ Auto-lock config found"
    cat /etc/snow/autolock.conf
else
    echo "✗ Auto-lock config missing"
    echo "Please check Snow integration setup"
fi

# Test auto-lock functionality
echo "Testing auto-lock..."
# Add your specific test commands here

echo "Script completed. Please review the output above."`;
    
    setScriptContent(sampleScript);
    setWorkMode('script');
  };

  // Toggle between demo and real mode
  const toggleDemoMode = () => {
    const newMode = !isDemoMode;
    setIsDemoMode(newMode);
    localStorage.setItem('isDemoMode', JSON.stringify(newMode));
    
    if (newMode === false) {
      // Switching to real mode - fetch data
      fetchRealData();
    } else {
      // Switching to demo mode - use mock data
      setTickets(mockTickets);
      setAiAnalysis(mockAnalysis);
      setAnalysisLoading(false);
    }
  };

  // Initialize with appropriate data
  React.useEffect(() => {
    if (isDemoMode) {
      setTickets(mockTickets);
      setAiAnalysis(mockAnalysis);
    } else {
      fetchRealData();
    }
  }, []);

  // Use tickets state instead of mockTickets
  const currentTickets = useMemo(() => {
    const tickets_to_use = tickets.length > 0 ? tickets : mockTickets;
    console.log('currentTickets computed, length:', tickets_to_use.length);
    return tickets_to_use;
  }, [tickets]);

  const filteredTickets = useMemo(() => {
    console.log('Filtering tickets. Search query:', searchQuery);
    console.log('Total tickets:', currentTickets.length);
    console.log('Component render triggered - checking if search input should maintain focus');
    
    if (!searchQuery.trim()) {
      console.log('No search query, returning all tickets');
      return currentTickets;
    }
    const query = searchQuery.toLowerCase().trim();
    const filtered = currentTickets.filter(t => {
      return (
        t.key.toLowerCase().includes(query) ||
        t.summary.toLowerCase().includes(query) ||
        (t.status && t.status.toLowerCase().includes(query)) ||
        (t.priority && t.priority.toLowerCase().includes(query))
      );
    });
    
    console.log('Filtered tickets count:', filtered.length);
    return filtered;
  }, [searchQuery, currentTickets]);

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

  const ticketCountText = useMemo(() => {
    return `${filteredTickets.length} tickets in your queue`;
  }, [filteredTickets.length]);

  const TicketsView = React.memo(() => {
    console.log('TicketsView rendering - searchQuery:', searchQuery, 'filteredTickets.length:', filteredTickets.length);
    
    return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Your Tickets</h1>
          <p className="text-slate-400">{ticketCountText}</p>
        </div>
        <div className="flex gap-3">
          {loading && (
            <div className="flex items-center gap-2 px-4 py-2 text-slate-400">
              <div className="w-4 h-4 border-2 border-slate-600 border-t-slate-400 rounded-full animate-spin"></div>
              Loading tickets...
            </div>
          )}
          <button 
            onClick={() => {
              console.log('AI Priority Analysis button clicked');
              console.log('isDemoMode:', isDemoMode);
              console.log('tickets.length:', tickets.length);
              console.log('aiAnalysis exists:', !!aiAnalysis);
              console.log('currentView before:', currentView);
              
              if (isDemoMode || (tickets.length > 0 && aiAnalysis)) {
                console.log('Setting currentView to analysis immediately');
                setCurrentView('analysis');
              } else if (!isDemoMode) {
                console.log('Fetching real data first, then setting analysis view');
                fetchRealData().then(() => {
                  console.log('Data fetched, now setting currentView to analysis');
                  setCurrentView('analysis');
                });
              }
            }}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-purple-800 transition-all disabled:opacity-50"
            disabled={loading || analysisLoading}
          >
            <Brain className="w-4 h-4" />
            AI Priority Analysis
            {(loading || analysisLoading) && (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin ml-1"></div>
            )}
          </button>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          ref={searchInputRef}
          id="ticket-search"
          name="ticketSearch"
          type="text"
          placeholder="Search tickets by key or summary..."
          className="w-full pl-10 pr-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-lg text-slate-300 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50"
          value={searchQuery}
          onChange={(e) => {
            console.log('Search input changed from:', searchQuery, 'to:', e.target.value);
            console.log('Input element id:', e.target.id, 'Input focused?', document.activeElement === e.target);
            const newValue = e.target.value;
            setSearchQuery(newValue);
            
            // Force focus back if it gets lost
            setTimeout(() => {
              if (searchInputRef.current && document.activeElement !== searchInputRef.current) {
                console.log('Focus lost, restoring...');
                searchInputRef.current.focus();
              }
            }, 0);
          }}
          onFocus={() => console.log('Search input focused')}
          onBlur={() => console.log('Search input blurred')}
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
          {filteredTickets.map(ticket => {
            const topPriorityKey = typeof aiAnalysis?.topPriority === 'string'
              ? aiAnalysis.topPriority
              : aiAnalysis?.topPriority?.key;
            return (
              <div 
                key={ticket.key} 
                className={`grid grid-cols-12 gap-4 p-4 hover:bg-slate-700/20 transition-colors cursor-pointer ${
                  ticket.key === topPriorityKey ? 'bg-purple-500/5 border-l-4 border-purple-500' : ''
                }`}
                onClick={() => {
                  setSelectedTicket(ticket.key);
                  setCurrentView('analysis');
                }}
              >
              <div className="col-span-2 font-mono text-slate-300 flex items-center">
                {ticket.key}
                <button
                  onClick={(e) => openTicketInJira(ticket.key, e)}
                  className="ml-2 text-slate-500 hover:text-purple-400"
                  title="Open in Jira"
                >
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
              <div className={`col-span-1 font-semibold ${getPriorityColor(ticket.priority)}`}>{ticket.priority}</div>
              <div className={`col-span-2 ${getStatusColor(ticket.status)}`}>{ticket.status}</div>
              <div className="col-span-1 text-slate-400">{ticket.age}</div>
              <div className="col-span-1 text-slate-400">{ticket.stale}</div>
              <div className="col-span-5 text-slate-300 truncate">{ticket.summary}</div>
            </div>
          );
        })}
        </div>
      </div>

      <div className="text-center">
        <p className="text-slate-500 text-sm">
          Click on any ticket or use <strong>AI Priority Analysis</strong> to get focused guidance
        </p>
      </div>
    </div>
    );
  });

  const AnalysisView = () => {
    console.log('AnalysisView rendering...');
    console.log('analysisLoading:', analysisLoading);
    console.log('aiAnalysis:', aiAnalysis);
    console.log('currentTickets:', currentTickets.length);
    console.log('selectedTicket:', selectedTicket);
    
    const topPriorityKey = typeof aiAnalysis?.topPriority === 'string'
      ? aiAnalysis.topPriority
      : aiAnalysis?.topPriority?.key;
    const focusTicket = currentTickets.find(t => t.key === (selectedTicket || topPriorityKey));

    console.log('topPriorityKey:', topPriorityKey);
    console.log('focusTicket:', focusTicket);

    if (analysisLoading) {
      console.log('Showing loading state');
      return (
        <div className="max-w-4xl mx-auto text-center py-8">
          <div className="w-8 h-8 border-2 border-slate-600 border-t-slate-400 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Analyzing your tickets with AI...</p>
        </div>
      );
    }

    if (!aiAnalysis) {
      console.log('No AI analysis available');
      return (
        <div className="max-w-4xl mx-auto text-center py-8">
          <p className="text-slate-400">No analysis available. Switch to Live Mode to get AI insights.</p>
          <button 
            onClick={() => {
              console.log('Fetching data from no-analysis state');
              fetchRealData();
            }}
            className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Load AI Analysis
          </button>
        </div>
      );
    }
    
    console.log('Rendering full analysis view');
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
                <button
                  onClick={(e) => openTicketInJira(focusTicket?.key, e)}
                  className="text-slate-500 hover:text-purple-400"
                  title="Open in Jira"
                >
                  <ExternalLink className="w-4 h-4" />
                </button>
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
            <div className="text-slate-300 mb-4 prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{aiAnalysis.urgency}</ReactMarkdown>
            </div>
            
            <h3 className="font-semibold text-slate-200 mb-3">Next concrete steps:</h3>
            <ol className="list-decimal list-inside space-y-2 text-slate-300 mb-4">
              {aiAnalysis.nextSteps.map((step, i) => (
                <li key={i} className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown 
                    components={{
                      p: ({ children }) => <span className="inline">{children}</span>
                    }}
                  >
                    {step}
                  </ReactMarkdown>
                </li>
              ))}
            </ol>
          </div>

          <div className="flex gap-4 mt-6">
            <button 
              onClick={() => setCurrentView('work')}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-purple-800 transition-all flex items-center justify-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              Let's work on this
            </button>
            <button 
              onClick={() => {
                setSelectedTicket('');
                setCurrentView('tickets');
                if (!isDemoMode) {
                  fetchRealData();
                }
              }}
              className="px-6 py-3 bg-slate-700/50 hover:bg-slate-600/50 border border-slate-600/30 rounded-lg text-slate-200 transition-colors flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Pick different ticket
            </button>
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
          <h3 className="font-semibold text-slate-200 mb-4">How I can help</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {aiAnalysis.howICanHelp.map((help, i) => (
              <button 
                key={i}
                onClick={() => handleHelpAction(help)}
                className="flex items-center gap-3 p-3 bg-slate-700/30 hover:bg-slate-600/40 rounded-lg transition-colors cursor-pointer text-left group"
              >
                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 group-hover:text-green-300" />
                <span className="text-slate-300 group-hover:text-slate-200">{help}</span>
              </button>
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
    const topPriorityKey = typeof aiAnalysis?.topPriority === 'string'
      ? aiAnalysis.topPriority
      : aiAnalysis?.topPriority?.key;
    const focusTicket = currentTickets.find(t => t.key === (selectedTicket || topPriorityKey));

    if (!aiAnalysis || analysisLoading) {
      return <div>Loading work analysis...</div>;
    }

    const workSteps = aiAnalysis.nextSteps || [];

    return (
      <div className="max-w-6xl mx-auto space-y-6">
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
          <div className="flex gap-3">
            <div className="flex bg-slate-800/50 border border-slate-700/50 rounded-lg p-1">
              <button
                onClick={() => setWorkMode('brainstorm')}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  workMode === 'brainstorm'
                    ? 'bg-purple-600 text-white'
                    : 'text-slate-400 hover:text-slate-300'
                }`}
              >
                <MessageCircle className="w-4 h-4 inline mr-1" />
                Brainstorm
              </button>
              <button
                onClick={() => setWorkMode('script')}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  workMode === 'script'
                    ? 'bg-purple-600 text-white'
                    : 'text-slate-400 hover:text-slate-300'
                }`}
              >
                <Code className="w-4 h-4 inline mr-1" />
                Script
              </button>
            </div>
            <button
              onClick={(e) => openTicketInJira(focusTicket?.key, e)}
              className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-600/50 border border-slate-600/30 rounded-lg text-slate-200 transition-colors"
              title="Open in Jira"
            >
              <ExternalLink className="w-4 h-4" />
              Open in Jira
            </button>
          </div>
        </div>

        {workMode === 'brainstorm' ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-200">AI Assistant Chat</h3>
                  <button
                    onClick={generateScript}
                    className="px-3 py-1 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded text-sm font-medium hover:from-purple-700 hover:to-purple-800 transition-all"
                  >
                    Generate Script
                  </button>
                </div>
                
                <div className="h-96 border border-slate-700/50 rounded-lg bg-slate-900/30 p-4 mb-4 overflow-y-auto">
                  {chatMessages.length === 0 ? (
                    <div className="text-slate-500 text-center py-8">
                      <MessageCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>Start a conversation about this ticket. Ask me anything!</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {chatMessages.map((msg, i) => (
                        <div key={i} className={`flex gap-3 ${
                          msg.type === 'user' ? 'justify-end' : 'justify-start'
                        }`}>
                          <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                            msg.type === 'user'
                              ? 'bg-purple-600 text-white'
                              : 'bg-slate-700 text-slate-200'
                          }`}>
                            {msg.content}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                
                <div className="flex gap-2">
                  <input
                    id="chat-input"
                    name="chatInput"
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Ask me about this ticket..."
                    className="flex-1 px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-300 placeholder-slate-500"
                  />
                  <button
                    onClick={handleSendMessage}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
                  >
                    Send
                  </button>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
                <h3 className="font-semibold text-slate-200 mb-4">Next concrete steps</h3>
                <ol className="list-decimal list-inside space-y-2 text-slate-300 text-sm">
                  {workSteps.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ol>
              </div>
              
              <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
                <h3 className="font-semibold text-slate-200 mb-4">Quick Actions</h3>
                <div className="space-y-2">
                  <button
                    onClick={() => handleHelpAction("Research the cause of the snow integration failure")}
                    className="w-full text-left px-3 py-2 bg-slate-700/30 hover:bg-slate-600/40 rounded text-sm text-slate-300 transition-colors"
                  >
                    🔍 Research integration failure
                  </button>
                  <button
                    onClick={() => handleHelpAction("Review the Jamf script logs")}
                    className="w-full text-left px-3 py-2 bg-slate-700/30 hover:bg-slate-600/40 rounded text-sm text-slate-300 transition-colors"
                  >
                    📋 Review script logs
                  </button>
                  <button
                    onClick={() => handleHelpAction("Develop a solution plan")}
                    className="w-full text-left px-3 py-2 bg-slate-700/30 hover:bg-slate-600/40 rounded text-sm text-slate-300 transition-colors"
                  >
                    💡 Develop solution plan
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-200">Generated Script</h3>
                <div className="flex gap-2">
                  <button
                    onClick={() => navigator.clipboard.writeText(scriptContent)}
                    className="px-3 py-1 bg-slate-700/50 hover:bg-slate-600/50 border border-slate-600/30 rounded text-sm text-slate-200 transition-colors"
                  >
                    Copy Script
                  </button>
                  <button
                    onClick={generateScript}
                    className="px-3 py-1 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded text-sm font-medium hover:from-purple-700 hover:to-purple-800 transition-all"
                  >
                    Regenerate
                  </button>
                </div>
              </div>
              
              {scriptContent ? (
                <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-4">
                  <pre className="text-green-400 text-sm font-mono whitespace-pre-wrap overflow-x-auto">
                    {scriptContent}
                  </pre>
                </div>
              ) : (
                <div className="text-slate-500 text-center py-8">
                  <Code className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>Click "Generate Script" to create a custom script for this ticket</p>
                </div>
              )}
            </div>
            
            {scriptContent && (
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
                <p className="text-amber-200">
                  <strong>⚠️ Review before use:</strong> This script is generated based on the ticket context. 
                  Please review and test it in a safe environment before running on production systems.
                </p>
              </div>
            )}
          </div>
        )}
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
            <button
              onClick={toggleDemoMode}
              className={`px-3 py-1 rounded-lg text-sm border transition-colors ${
                isDemoMode 
                  ? 'bg-amber-600/20 text-amber-300 border-amber-600/30 hover:bg-amber-600/30' 
                  : 'bg-green-600/20 text-green-300 border-green-600/30 hover:bg-green-600/30'
              }`}
            >
              {isDemoMode ? 'Demo Mode' : 'Live Mode'}
            </button>
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