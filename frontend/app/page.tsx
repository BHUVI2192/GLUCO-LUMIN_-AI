"use client";

import { useState, useRef, useEffect } from 'react';
import { useWebSerial } from '@/hooks/useWebSerial';
import { registerPatient, uploadRawData, getResult, PatientData } from '@/lib/api';

export default function Home() {
    // State
    const [formData, setFormData] = useState<PatientData>({
        patient_id: '',
        name: '',
        age: 0,
        sex: 'Male',
        bmi: 0,
        skin_tone: 'Type I',
    });
    const [visitId, setVisitId] = useState<string | null>(null);
    const [scanStatus, setScanStatus] = useState<'IDLE' | 'SCANNING' | 'PROCESSING' | 'DONE'>('IDLE');
    const [linesBuffer, setLinesBuffer] = useState<string[]>([]);
    const [result, setResult] = useState<{ glucose: number, classification: string } | null>(null);
    const [timeLeft, setTimeLeft] = useState(30);

    const { isSupported, isConnected, connect, disconnect, startReading, stopReading, mockSimulate } = useWebSerial();
    const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

    // Handlers
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await registerPatient(formData);
            setVisitId(res.visit_id);
            alert(`Patient Registered! Visit ID: ${res.visit_id}`);
        } catch (err) {
            console.error(err);
            alert('Registration Failed');
        }
    };

    const handleStartScan = async () => {
        if (!visitId) {
            alert("Please register patient first");
            return;
        }

        setScanStatus('SCANNING');
        setLinesBuffer([]); // Clear previous
        setTimeLeft(30); // Reset Timer
        const accumulatedLines: string[] = [];

        // Timer Logic
        const timer = setInterval(() => {
            setTimeLeft((prev) => {
                if (prev <= 1) {
                    clearInterval(timer);
                    // Force Stop
                    if (isConnected) stopReading();
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        const onData = (line: string) => {
            accumulatedLines.push(line);
            setLinesBuffer(prev => [...prev.slice(-19), line]);
        };

        const onComplete = async () => {
            clearInterval(timer); // Ensure timer stops if completed early
            setScanStatus('PROCESSING');
            // Upload Data
            try {
                await uploadRawData(accumulatedLines);
                startPolling();
            } catch (err) {
                console.error("Upload failed", err);
                setScanStatus('IDLE');
                alert("Upload failed");
            }
        };

        if (isConnected) {
            await startReading(visitId, onData, onComplete);
        } else {
            // Fallback or Demo logic
            if (confirm("Device not connected. Run Simulation?")) {
                mockSimulate(visitId, onData, onComplete);
            } else {
                setScanStatus('IDLE');
            }
        }
    };

    const startPolling = () => {
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

        pollIntervalRef.current = setInterval(async () => {
            if (!visitId) return;
            try {
                const res = await getResult(visitId);
                if (res.status === 'DONE') {
                    setResult({ glucose: res.glucose, classification: res.classification });
                    setScanStatus('DONE');
                    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
                }
            } catch (err) {
                console.log("Polling error", err);
            }
        }, 2000);
    };

    const handleReset = () => {
        setVisitId(null);
        setScanStatus('IDLE');
        setLinesBuffer([]);
        setResult(null);
        setFormData({
            patient_id: '',
            name: '',
            age: 0,
            sex: 'Male',
            bmi: 0,
            skin_tone: 'Type I',
        });
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };

    // Render Helpers
    const getResultColor = (classification: string) => {
        if (classification === 'High' || classification === 'Low') return 'text-red-600';
        if (classification === 'Normal') return 'text-green-600';
        return 'text-gray-900';
    };

    return (
        <main className="min-h-screen p-4 md:p-8 max-w-md mx-auto bg-white shadow-xl rounded-xl my-4">
            <header className="mb-6 flex justify-between items-center">
                <h1 className="text-2xl font-bold text-slate-800">GlucoLumin Validator</h1>
                <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} title={isConnected ? "Device Connected" : "Device Disconnected"}></div>
            </header>

            {/* RESULT VIEW */}
            {scanStatus === 'DONE' && result && (
                <div className="text-center py-10 animate-in fade-in">
                    <h2 className="text-xl text-slate-600 mb-2">Estimated Glucose</h2>
                    <div className={`text-6xl font-black ${getResultColor(result.classification)} mb-4`}>
                        {result.glucose} <span className="text-xl font-medium text-slate-500">mg/dL</span>
                    </div>
                    <div className={`inline-block px-4 py-1 rounded-full text-white font-bold mb-8 ${result.classification === 'Normal' ? 'bg-green-500' : 'bg-red-500'}`}>
                        {result.classification}
                    </div>

                    <button onClick={handleReset} className="w-full bg-slate-800 text-white py-3 rounded-lg font-semibold hover:bg-slate-700 transition">
                        Scan Next Patient
                    </button>
                </div>
            )}

            {/* SCANNING / REGISTER VIEW */}
            {scanStatus !== 'DONE' && (
                <div className="space-y-6">
                    {/* Connection Panel */}
                    {!visitId && (
                        <div className="bg-slate-100 p-4 rounded-lg flex justify-between items-center">
                            <span className="text-sm font-medium text-slate-600">Hardware Interface</span>
                            {isConnected ? (
                                <button onClick={disconnect} className="text-xs bg-red-100 text-red-600 px-3 py-1 rounded border border-red-200">Disconnect</button>
                            ) : (
                                <button onClick={connect} disabled={!isSupported} className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 disabled:opacity-50">
                                    {isSupported ? 'Connect Device' : 'Serial Not Supported'}
                                </button>
                            )}
                        </div>
                    )}

                    {/* Registration Form */}
                    {!visitId ? (
                        <form onSubmit={handleRegister} className="space-y-4">
                            <div>
                                <label className="block text-xs font-semibold text-slate-500 uppercase">Patient ID</label>
                                <input required name="patient_id" value={formData.patient_id} onChange={handleInputChange} className="w-full p-2 border border-slate-300 rounded mt-1 text-slate-900" placeholder="P-101" />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-500 uppercase">Name</label>
                                <input required name="name" value={formData.name} onChange={handleInputChange} className="w-full p-2 border border-slate-300 rounded mt-1 text-slate-900" placeholder="John Doe" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-semibold text-slate-500 uppercase">Age</label>
                                    <input required type="number" name="age" value={formData.age} onChange={handleInputChange} className="w-full p-2 border border-slate-300 rounded mt-1 text-slate-900" />
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-slate-500 uppercase">BMI</label>
                                    <input required type="number" step="0.1" name="bmi" value={formData.bmi} onChange={handleInputChange} className="w-full p-2 border border-slate-300 rounded mt-1 text-slate-900" />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-semibold text-slate-500 uppercase">Sex</label>
                                    <select name="sex" value={formData.sex} onChange={handleInputChange} className="w-full p-2 border border-slate-300 rounded mt-1 text-slate-900">
                                        <option>Male</option>
                                        <option>Female</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-slate-500 uppercase">Skin Tone</label>
                                    <select name="skin_tone" value={formData.skin_tone} onChange={handleInputChange} className="w-full p-2 border border-slate-300 rounded mt-1 text-slate-900">
                                        <option>Type I</option>
                                        <option>Type II</option>
                                        <option>Type III</option>
                                        <option>Type IV</option>
                                        <option>Type V</option>
                                        <option>Type VI</option>
                                    </select>
                                </div>
                            </div>
                            <button type="submit" className="w-full bg-blue-600 text-white py-3 rounded-lg font-bold shadow-lg hover:bg-blue-700 active:scale-95 transition">
                                Start Session
                            </button>
                        </form>
                    ) : (
                        <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                            <div className="flex justify-between mb-2">
                                <span className="font-bold text-blue-900">Visit ID:</span>
                                <span className="font-mono text-blue-700">{visitId}</span>
                            </div>
                            <div className="text-sm text-blue-800">{formData.name} ({formData.age}y)</div>
                        </div>
                    )}

                    {/* Controls */}
                    {visitId && scanStatus === 'IDLE' && (
                        <button onClick={handleStartScan} className="w-full h-32 rounded-xl flex flex-col items-center justify-center bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-xl hover:shadow-2xl transition transform hover:-translate-y-1">
                            <span className="text-4xl mb-2">📡</span>
                            <span className="text-xl font-bold">INITIATE SCAN</span>
                            <span className="text-sm opacity-80 mt-1">Make sure sensor is active</span>
                        </button>
                    )}

                    {/* Monitor */}
                    {scanStatus === 'SCANNING' && (
                        <div className="space-y-4">
                            <div className="text-center">
                                <div className="text-indigo-600 font-semibold mb-2">Scanning in progress...</div>
                                <div className="w-full bg-slate-200 rounded-full h-4 overflow-hidden shadow-inner relative">
                                    <div
                                        className="bg-gradient-to-r from-blue-500 to-indigo-600 h-full transition-all duration-1000 ease-linear"
                                        style={{ width: `${((30 - timeLeft) / 30) * 100}%` }}
                                    ></div>
                                </div>
                                <div className="text-sm text-slate-500 mt-1 font-mono">{timeLeft}s Remaining</div>
                            </div>

                            <div className="bg-black rounded-lg p-4 h-32 overflow-hidden font-mono text-green-400 text-xs shadow-inner opacity-80">
                                {linesBuffer.map((line, i) => (
                                    <div key={i}>{line}</div>
                                ))}
                                <div className="animate-pulse">_</div>
                            </div>
                        </div>
                    )}

                    {/* Processing */}
                    {scanStatus === 'PROCESSING' && (
                        <div className="text-center py-12">
                            <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
                            <h3 className="text-lg font-semibold text-slate-700">Analyzing Signal</h3>
                            <p className="text-slate-500 text-sm">Running ML Pipeline...</p>
                        </div>
                    )}
                </div>
            )}
        </main>
    );
}
