import React, { useState, useMemo, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { ChevronRight, AlertTriangle, Clock, User, Calendar, Search, Target, Brain, ArrowRight, CheckCircle, Play, ExternalLink, Sparkles, RefreshCw, Code } from 'lucide-react';
import { API_BASE_URL } from './config';

const PersonalTicketAssistant = () => {
  const [currentView, setCurrentView] = useState('tickets'); // tickets, analysis
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
  // Removed work mode state variables - no longer needed
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
      const response = await fetch(`${API_BASE_URL}/api/session/start`, {
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
  
  // Fetch analysis for a specific ticket
  const fetchTicketAnalysis = async (ticketKey) => {
    setAnalysisLoading(true);
    try {
      console.log(`Fetching analysis for ticket: ${ticketKey}`);
      const response = await fetch(`${API_BASE_URL}/api/ticket/${ticketKey}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log(`Analysis received for ${ticketKey}:`, data);
        
        // Update the analysis state with ticket-specific data
        setAiAnalysis({
          topPriority: ticketKey,
          reasoning: data.analysis.priority_reasoning || '',
          urgency: data.analysis.summary || '',
          nextSteps: data.analysis.next_steps || [],
          howICanHelp: data.analysis.can_help_with || [],
          context: data.analysis.context || '',
          ticketSpecific: true, // Flag to indicate this is ticket-specific
          analyzedTicket: data.ticket || null
        });
      } else {
        console.error(`Failed to fetch analysis for ${ticketKey}:`, response.status);
        // Fallback to basic ticket info
        const ticket = tickets.find(t => t.key === ticketKey);
        if (ticket) {
          setAiAnalysis({
            topPriority: ticketKey,
            reasoning: `Analysis for ${ticketKey}: ${ticket.summary}`,
            urgency: `Priority ${ticket.priority} ticket, ${ticket.age} old, ${ticket.stale} since last update.`,
            nextSteps: [
              'Review ticket details and requirements',
              'Identify blockers or dependencies',
              'Plan next actions based on status'
            ],
            howICanHelp: [
              'Research related documentation',
              'Help break down tasks into steps',
              'Assist with planning'
            ],
            context: `This ticket is part of your current workload and has been ${ticket.status} for ${ticket.stale}.`,
            ticketSpecific: true,
            analyzedTicket: ticket
          });
        }
      }
    } catch (error) {
      console.error(`Error fetching analysis for ${ticketKey}:`, error);
      // Fallback to basic ticket info when there's an error
      const ticket = tickets.find(t => t.key === ticketKey);
      if (ticket) {
        setAiAnalysis({
          topPriority: ticketKey,
          reasoning: `Analysis for ${ticketKey}: ${ticket.summary}`,
          urgency: `Priority ${ticket.priority} ticket, ${ticket.age} old, ${ticket.stale} since last update.`,
          nextSteps: [
            'Review ticket details and requirements',
            'Identify blockers or dependencies',
            'Plan next actions based on status'
          ],
          howICanHelp: [
            'Research related documentation',
            'Help break down tasks into steps',
            'Assist with planning'
          ],
          context: `This ticket is part of your current workload and has been ${ticket.status} for ${ticket.stale}.`,
          ticketSpecific: true,
          analyzedTicket: ticket
        });
      }
    } finally {
      setAnalysisLoading(false);
    }
  };
  
  // Open ticket in Jira
  const openTicketInJira = async (ticketKey, e) => {
    e.stopPropagation(); // Prevent triggering the parent onClick
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/ticket/${ticketKey}/url`);
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
    // Show chat interface without navigating away from analysis view
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

  // Contextual Action Engine - analyzes ticket metadata to suggest specific actions
  const getContextualRecommendation = (ticket, analysis, demoMode) => {
    if (!ticket || !analysis) {
      return (
        <div className="text-center py-8">
          <p className="text-slate-400">Loading contextual recommendations...</p>
        </div>
      );
    }

    // Rule-based contextual logic
    const getContextualAction = (ticket) => {
      const age = parseInt(ticket.age?.replace('d', '') || '0');
      const stale = parseInt(ticket.stale?.replace('d', '') || '0');
      const priority = ticket.priority?.toLowerCase() || '';
      const summary = ticket.summary?.toLowerCase() || '';
      const status = ticket.status?.toLowerCase() || '';
      
      // Integration failure + very old = verify if issue still exists
      if (summary.includes('integration') && summary.includes('fail') && age > 180) {
        return {
          title: "Verify Issue Still Exists",
          reasoning: `This ${age}-day-old integration issue may have been automatically resolved. Let's verify the current state before investing effort.`,
          primary: {
            text: "Test Current Integration Status",
            description: "Check if the ServiceNow-Jamf auto-lock is still failing",
            action: "Test the current ServiceNow-Jamf integration to see if auto-lock failures are still occurring"
          },
          secondary: {
            text: "Research Recent Changes", 
            description: "Look for system updates that may have resolved this",
            action: "Check ServiceNow and Jamf system logs for recent changes that might have fixed the integration"
          }
        };
      }
      
      // P1/Critical + old = escalate or close decision
      if (priority.includes('p1') && age > 90) {
        return {
          title: "Escalate or Close Decision Needed",
          reasoning: `This P1 ticket is ${age} days old. Either it needs immediate escalation or the priority should be re-evaluated.`,
          primary: {
            text: "Escalate for Immediate Action",
            description: "Get stakeholder attention for this aging P1",
            action: "Escalate this P1 ticket to management due to its age and lack of progress"
          },
          secondary: {
            text: "Re-assess Priority Level",
            description: "Check if this is truly still P1 priority",
            action: "Review with stakeholders whether this ticket is still P1 priority given its age"
          }
        };
      }
      
      // In Progress + very stale = check status with assignee
      if (status.includes('progress') && stale > 30) {
        return {
          title: "Check Progress Status",
          reasoning: `This ticket has been "In Progress" but stale for ${stale} days. Let's get a status update.`,
          primary: {
            text: "Get Status from Assignee",
            description: "Find out what's blocking progress",
            action: `Contact ${ticket.assignee || 'the assignee'} to get current status and identify blockers`
          },
          secondary: {
            text: "Review Recent Activity", 
            description: "Check for updates in comments or related tickets",
            action: "Review recent comments and related tickets for context on current progress"
          }
        };
      }
      
      // Security/vulnerability + any age = check for patch
      if (summary.includes('vulnerabilit') || summary.includes('security')) {
        return {
          title: "Security Issue - Check for Patch",
          reasoning: "Security vulnerabilities should be addressed quickly. Let's check if a patch or fix is available.",
          primary: {
            text: "Check for Available Patch",
            description: "Look for security updates or fixes",
            action: "Research if a security patch or update is available for this vulnerability"
          },
          secondary: {
            text: "Assess Impact & Urgency",
            description: "Determine blast radius and criticality",
            action: "Assess the security impact and determine if this needs emergency patching"
          }
        };
      }
      
      // VOC_Feedback (customer complaint) = reproduce issue
      if (ticket.labels?.includes('VOC_Feedback') || summary.includes('customer') || summary.includes('user')) {
        return {
          title: "Customer Impact - Reproduce Issue",
          reasoning: "This appears to impact users directly. Let's reproduce the issue to understand the customer experience.",
          primary: {
            text: "Reproduce Customer Issue",
            description: "Experience the problem from user perspective",
            action: "Attempt to reproduce the customer-reported issue to understand the impact"
          },
          secondary: {
            text: "Contact Affected Users",
            description: "Get more details from customers",
            action: "Reach out to affected customers for additional context and impact assessment"
          }
        };
      }
      
      // Fresh ticket (< 7 days) = gather context
      if (age < 7) {
        return {
          title: "Fresh Ticket - Gather Context",
          reasoning: `This ${age}-day-old ticket needs initial investigation to understand requirements and scope.`,
          primary: {
            text: "Investigate Requirements",
            description: "Understand what needs to be done",
            action: "Review ticket details, requirements, and gather context from stakeholders"
          },
          secondary: {
            text: "Check for Dependencies",
            description: "Look for related tickets or blockers",
            action: "Search for related tickets and identify any dependencies or blockers"
          }
        };
      }
      
      // Fallback for any ticket
      return {
        title: "Analyze Current Status",
        reasoning: `Let's get up to speed on this ${priority} ticket and identify the best path forward.`,
        primary: {
          text: "Review Current Status",
          description: "Understand where things stand",
          action: `Review ${ticket.key} status, recent activity, and identify next steps`
        },
        secondary: {
          text: "Identify Blockers",
          description: "Find what's preventing progress", 
          action: "Identify any blockers, dependencies, or issues preventing progress"
        }
      };
    };

    // Use demo-specific logic for CPE-3117 or contextual logic for live tickets
    let recommendation;
    if (demoMode && ticket.key === 'CPE-3117') {
      recommendation = {
        title: "Integration Issue - Verify Current State",
        reasoning: "This 210-day-old ServiceNow-Jamf integration ticket needs verification before proceeding with fixes.",
        primary: {
          text: "Test Current Auto-Lock Status",
          description: "Check if the integration is still failing",
          action: "Test the ServiceNow-Jamf integration to verify if auto-lock failures are still occurring"
        },
        secondary: {
          text: "Check CPE-3043 Dependency",
          description: "Verify if the root cause ticket was resolved",
          action: "Check status of CPE-3043 dependency ticket to see if it was resolved"
        }
      };
    } else {
      recommendation = getContextualAction(ticket);
    }

    return (
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-slate-100 mb-2">🎯 {recommendation.title}</h2>
          <p className="text-slate-400 max-w-2xl mx-auto">{recommendation.reasoning}</p>
        </div>
        
        <div className="grid gap-4 max-w-2xl mx-auto">
          <button
            onClick={() => handleHelpAction(recommendation.primary.action)}
            className="w-full p-6 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 border-2 border-blue-500/50 rounded-xl text-left transition-all group"
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-xl font-semibold text-white mb-2">{recommendation.primary.text}</h3>
                <p className="text-blue-100 text-sm">{recommendation.primary.description}</p>
              </div>
              <ArrowRight className="w-6 h-6 text-blue-200 group-hover:text-white group-hover:translate-x-1 transition-all" />
            </div>
          </button>
          
          <button
            onClick={() => handleHelpAction(recommendation.secondary.action)}
            className="w-full p-6 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 border-2 border-purple-500/50 rounded-xl text-left transition-all group"
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-xl font-semibold text-white mb-2">{recommendation.secondary.text}</h3>
                <p className="text-purple-100 text-sm">{recommendation.secondary.description}</p>
              </div>
              <ArrowRight className="w-6 h-6 text-purple-200 group-hover:text-white group-hover:translate-x-1 transition-all" />
            </div>
          </button>
        </div>
      </div>
    );
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
              console.log('AI Workload Analysis button clicked');
              console.log('isDemoMode:', isDemoMode);
              console.log('tickets.length:', tickets.length);
              console.log('aiAnalysis exists:', !!aiAnalysis);
              console.log('currentView before:', currentView);
              
              // Clear selected ticket for workload analysis
              setSelectedTicket('');
              
              if (isDemoMode || (tickets.length > 0 && aiAnalysis)) {
                console.log('Setting currentView to analysis immediately');
                // Clear ticket-specific flag for workload analysis
                if (aiAnalysis?.ticketSpecific) {
                  setAiAnalysis({...aiAnalysis, ticketSpecific: false});
                }
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
            AI Workload Analysis
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
                  // Fetch analysis specific to this ticket
                  fetchTicketAnalysis(ticket.key);
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
          <strong>Click any ticket</strong> for specific analysis, or use <strong>AI Workload Analysis</strong> for overall prioritization
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
    
    // Enhanced priority logic implementation
    const calculatePriorityTickets = () => {
      if (!tickets || tickets.length === 0) return [];
      
      // Clone the tickets array to avoid modifying the original
      const ticketsCopy = [...tickets];
      
      // Calculate priority score for each ticket
      const scoredTickets = ticketsCopy.map(ticket => {
        let score = 0;
        let reasoning = '';
        
        // Age logic
        const age = parseInt(ticket.age);
        if (age > 180) {
          score += 20;
          reasoning = `This ${age}-day-old ${ticket.priority === 'P1' ? 'security ' : ''}ticket is either completely irrelevant now or represents a massive oversight. Verify and close.`;
        }
        
        // Status + staleness
        const stale = parseInt(ticket.stale);
        if (ticket.status === 'In Progress' && stale > 21) {
          score += 30;
          reasoning = `In Progress but stale for ${stale} days. This ${ticket.priority} ${ticket.priority === 'P1' ? 'security ' : ''}update shouldn't be sitting idle. Follow up on status or roadblocks.`;
        }
        
        // Priority + age mismatch
        if (ticket.priority === 'P1' && age > 30) {
          score += 40;
          reasoning = `${ticket.priority} ${ticket.summary.toLowerCase().includes('security') ? 'security ' : ''}ticket open for ${age} days requires immediate attention. ${age > 90 ? 'Extremely delayed resolution.' : ''}`;
        }
        
        // Special labels (simulated)
        const hasVOCLabel = ticket.key === 'CPE-3117'; // Simulate VOC label for this example
        if (hasVOCLabel) {
          score += 25;
          reasoning = `${age} days old with VOC feedback label suggests customer impact. Before investigating, verify if the issue still exists - many integration problems resolve themselves.`;
        }
        
        return {
          ...ticket,
          priorityScore: score,
          reasoning: reasoning || `This ticket requires routine attention based on its ${ticket.priority} priority.`,
          hasVOCLabel: hasVOCLabel
        };
      });
      
      // Sort by priority score (descending)
      scoredTickets.sort((a, b) => b.priorityScore - a.priorityScore);
      
      // Return top 3 tickets
      return scoredTickets.slice(0, 3);
    };
    
    // Get top priority tickets
    const priorityTickets = isDemoMode 
      ? [
          {
            key: 'VMR-320',
            priority: 'P1',
            status: 'To Do',
            age: '1484d',
            stale: '1470d',
            summary: 'GOTS-Critical-152190: Google Chrome < 92.0.4515.131 Multiple Vulnerabilities',
            priorityScore: 100,
            reasoning: 'This 1484-day-old security ticket is either completely irrelevant now or represents a massive oversight. Chrome has been updated dozens of times since 2021. Verify and close.',
            hasVOCLabel: false
          },
          {
            key: 'CPE-3117',
            priority: 'P3',
            status: 'To Do',
            age: '212d', 
            stale: '105d',
            summary: 'Auto lock macs via snow integration failure',
            priorityScore: 85,
            reasoning: '212 days old with VOC feedback label suggests customer impact. Before investigating, verify if the auto-lock issue still exists - many integration problems resolve themselves.',
            hasVOCLabel: true
          },
          {
            key: 'CPE-3313',
            priority: 'P1',
            status: 'In Progress',
            age: '101d',
            stale: '23d',
            summary: 'Update Mac Netskope Client to v126',
            priorityScore: 70,
            reasoning: "In Progress but stale for 23 days. This P1 security update shouldn't be sitting idle. Follow up on status or roadblocks.",
            hasVOCLabel: false
          }
        ]
      : calculatePriorityTickets();
    
    return (
      <div className="max-w-4xl mx-auto">
        <div className="header mb-10 text-center">
          <button 
            onClick={() => setCurrentView('tickets')}
            className="back-link text-slate-500 hover:text-slate-400 text-sm mb-5 flex items-center gap-1 mx-auto"
          >
            <ChevronRight className="w-4 h-4 rotate-180" />
            Back to tickets
          </button>
          <h1 className="text-3xl font-semibold text-slate-100 mb-2">
            Today's Priorities
          </h1>
          <p className="subtitle text-slate-400">
            AI analysis of your {tickets.length} tickets based on urgency and context
          </p>
        </div>
        
        {/* Priority Tickets Section */}
        <div className="priority-list bg-slate-800 border border-slate-600 rounded-xl overflow-hidden">
          {priorityTickets.map((ticket, index) => (
            <div 
              key={ticket.key}
              className={`priority-item p-6 relative ${index !== priorityTickets.length - 1 ? 'border-b border-slate-600' : ''} ${
                index === 0 
                  ? 'urgent bg-gradient-to-r from-red-500/10 to-red-500/5 border-l-4 border-l-red-500 transform scale-[1.02] shadow-lg' 
                  : 'normal bg-gradient-to-r from-slate-700/50 to-slate-600/30 border-l-4 border-l-slate-500'
              }`}
            >
              <div className={`priority-number absolute top-4 right-5 w-8 h-8 rounded-full flex items-center justify-center font-semibold text-sm ${
                index === 0 ? 'bg-red-900/30 text-red-400' : 'bg-slate-700 text-slate-400'
              }`}>
                {index + 1}
              </div>
              
              <div className="ticket-id font-mono text-slate-400 text-sm mb-2">
                {ticket.key}
              </div>
              
              <div className="ticket-title text-lg font-semibold text-slate-100 mb-3 pr-10">
                {ticket.summary}
              </div>
              
              <div className="reasoning text-slate-300 text-[15px] mb-4">
                {ticket.reasoning}
              </div>
              
              <div className="metadata flex gap-4 text-sm text-slate-500 mb-4">
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {ticket.age} old
                </span>
                <span className="flex items-center gap-1">
                  <AlertTriangle className="w-4 h-4" />
                  {ticket.priority}
                </span>
                <span className="flex items-center gap-1">
                  <Target className="w-4 h-4" />
                  {ticket.status}
                </span>
                {ticket.hasVOCLabel && (
                  <span className="flex items-center gap-1">
                    <User className="w-4 h-4" />
                    VOC_Feedback
                  </span>
                )}
              </div>
              
              <div className="actions">
                <button
                  onClick={(e) => openTicketInJira(ticket.key, e)}
                  className={`btn px-4 py-2 rounded-lg font-medium text-sm ${
                    index === 0 
                      ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >
                  View Details
                </button>
              </div>
            </div>
          ))}
        </div>
        
        <div className="summary bg-slate-800 border border-slate-600 rounded-xl p-5 mt-8 text-center">
          <p className="text-slate-400 mb-4">Focus on these {priorityTickets.length} tickets today. The rest can wait or may not need immediate attention.</p>
          <button 
            onClick={() => {
              setCurrentView('tickets');
              if (!isDemoMode) {
                fetchRealData();
              }
            }}
            className="btn-back bg-slate-700 hover:bg-slate-600 border border-slate-600 text-slate-200 px-5 py-2.5 rounded-lg font-medium text-sm transition-colors"
          >
            Back to all tickets
          </button>
        </div>
      </div>
    );
  };

  // Removed WorkView - contextual recommendations now appear directly in AnalysisView

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
      </main>
    </div>
  );
};

export default PersonalTicketAssistant;