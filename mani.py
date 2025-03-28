from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for API requests

class Process:
    def __init__(self, pid, arrival, burst, priority=0):
        self.pid = pid
        self.arrival = arrival
        self.burst = burst
        self.priority = priority
        self.remaining = burst
        self.start_time = None
        self.completion_time = None
        self.waiting_time = 0
        self.turnaround_time = 0

def fcfs_scheduling(processes):
    processes.sort(key=lambda p: p.arrival)
    time = 0
    gantt_chart = []
    for process in processes:
        if time < process.arrival:
            time = process.arrival
        process.start_time = time
        time += process.burst
        process.completion_time = time
        process.turnaround_time = process.completion_time - process.arrival
        process.waiting_time = process.turnaround_time - process.burst
        gantt_chart.append((process.pid, process.start_time, process.completion_time))
    return gantt_chart, processes

def sjf_preemptive(processes):
    time = 0
    gantt_chart = []
    completed = []
    remaining = processes.copy()
    while remaining:
        available = [p for p in remaining if p.arrival <= time]
        if not available:
            time += 1
            continue
        current = min(available, key=lambda p: p.remaining)
        current.remaining -= 1
        gantt_chart.append((current.pid, time, time + 1))
        if current.remaining == 0:
            current.completion_time = time + 1
            current.turnaround_time = current.completion_time - current.arrival
            current.waiting_time = current.turnaround_time - current.burst
            completed.append(current)
            remaining.remove(current)
        time += 1
    return gantt_chart, completed

def priority_preemptive(processes):
    time = 0
    gantt_chart = []
    completed = []
    remaining = processes.copy()
    while remaining:
        available = [p for p in remaining if p.arrival <= time]
        if not available:
            time += 1
            continue
        current = min(available, key=lambda p: p.priority)
        current.remaining -= 1
        gantt_chart.append((current.pid, time, time + 1))
        if current.remaining == 0:
            current.completion_time = time + 1
            current.turnaround_time = current.completion_time - current.arrival
            current.waiting_time = current.turnaround_time - current.burst
            completed.append(current)
            remaining.remove(current)
        time += 1
    return gantt_chart, completed

def round_robin_scheduling(processes, quantum):
    queue = processes.copy()
    time = 0
    gantt_chart = []
    completed = []
    while queue:
        process = queue.pop(0)
        if time < process.arrival:
            time = process.arrival
        start = time
        exec_time = min(process.remaining, quantum)
        time += exec_time
        process.remaining -= exec_time
        gantt_chart.append((process.pid, start, time))
        
        if process.remaining > 0:
            queue.append(process)
        else:
            process.completion_time = time
            process.turnaround_time = process.completion_time - process.arrival
            process.waiting_time = process.turnaround_time - process.burst
            completed.append(process)
    return gantt_chart, completed

@app.route('/')
def index():
    return render_template('manikanta.html')

@app.route('/schedule', methods=['POST'])
def schedule():
    try:
        data = request.json
        if not data or 'algorithm' not in data or 'processes' not in data:
            return jsonify({"error": "Missing required fields"}), 400
            
        algorithm = data['algorithm']
        quantum = data.get('quantum', 2)
        processes_data = data['processes']
        
        processes = [Process(p['pid'], p['arrival'], p['burst'], p.get('priority', 0)) 
                    for p in processes_data]
        
        if algorithm == "FCFS":
            gantt_chart, result_processes = fcfs_scheduling(processes)
        elif algorithm == "SJF-Preemptive":
            gantt_chart, result_processes = sjf_preemptive(processes)
        elif algorithm == "Priority-Preemptive":
            gantt_chart, result_processes = priority_preemptive(processes)
        elif algorithm == "RR":
            if quantum < 1:
                return jsonify({"error": "Quantum must be positive"}), 400
            gantt_chart, result_processes = round_robin_scheduling(processes, quantum)
        else:
            return jsonify({"error": "Invalid algorithm"}), 400

        result = {
            "gantt_chart": gantt_chart,
            "avg_waiting_time": sum(p.waiting_time for p in result_processes) / len(result_processes),
            "avg_turnaround_time": sum(p.turnaround_time for p in result_processes) / len(result_processes),
            "processes": [{"pid": p.pid, "waiting_time": p.waiting_time, 
                            "turnaround_time": p.turnaround_time} for p in result_processes]
        }
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)
