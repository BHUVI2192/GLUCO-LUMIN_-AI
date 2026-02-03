import { useState, useRef, useEffect } from 'react';

interface SerialHook {
    isSupported: boolean;
    isConnected: boolean;
    connect: () => Promise<void>;
    disconnect: () => Promise<void>;
    startReading: (visitId: string, onData: (line: string) => void, onComplete: () => void) => Promise<void>;
    stopReading: () => void;
    mockSimulate: (visitId: string, onData: (line: string) => void, onComplete: () => void) => void;
}

export const useWebSerial = (): SerialHook => {
    const [isSupported, setIsSupported] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const portRef = useRef<any>(null);
    const readerRef = useRef<any>(null);
    const keepReadingRef = useRef(false);

    useEffect(() => {
        setIsSupported('serial' in navigator);
    }, []);

    const connect = async () => {
        if (!isSupported) return;
        try {
            const port = await (navigator as any).serial.requestPort();
            await port.open({ baudRate: 9600 });
            portRef.current = port;
            setIsConnected(true);
        } catch (err) {
            console.error("Failed to connect:", err);
        }
    };

    const disconnect = async () => {
        keepReadingRef.current = false;
        if (readerRef.current) {
            await readerRef.current.cancel();
        }
        if (portRef.current) {
            await portRef.current.close();
            portRef.current = null;
        }
        setIsConnected(false);
    };

    const startReading = async (visitId: string, onData: (line: string) => void, onComplete: () => void) => {
        if (!portRef.current || !portRef.current.readable) return;

        keepReadingRef.current = true;
        const textDecoder = new TextDecoderStream();
        const readableStreamClosed = portRef.current.readable.pipeTo(textDecoder.writable);
        const reader = textDecoder.readable.getReader();
        readerRef.current = reader;

        // Send START command
        const writer = portRef.current.writable.getWriter();
        await writer.write(new TextEncoder().encode(`START_SCAN; VISIT_ID=${visitId}\n`));
        writer.releaseLock();

        try {
            let buffer = "";
            while (keepReadingRef.current) {
                const { value, done } = await reader.read();
                if (done) break;
                if (value) {
                    buffer += value;
                    const lines = buffer.split('\n');
                    // Process all complete lines
                    buffer = lines.pop() || ""; // Keep the last incomplete fragment

                    for (const line of lines) {
                        const trimmed = line.trim();
                        if (trimmed === "END_SCAN") {
                            keepReadingRef.current = false;
                            onComplete();
                            break;
                        }
                        if (trimmed) {
                            onData(trimmed);
                        }
                    }
                }
            }
        } catch (err) {
            console.error("Error reading:", err);
        } finally {
            reader.releaseLock();
            await readableStreamClosed.catch(() => { }); // Ignore stream closure errors
        }
    };

    const stopReading = () => {
        keepReadingRef.current = false;
    };

    // Mock Simulation
    const mockSimulate = (visitId: string, onData: (line: string) => void, onComplete: () => void) => {
        console.log("Starting Simulation...");
        let sampleIndex = 0;
        const interval = setInterval(() => {
            if (sampleIndex >= 300) { // Simulate 300 samples instead of 3000 to be faster for demo
                clearInterval(interval);
                onComplete();
                return;
            }
            // Generate dummy signal: Sine wave + noise
            const signal = Math.sin(sampleIndex * 0.1) + Math.random() * 0.1;
            const line = `${visitId},${sampleIndex},${signal.toFixed(4)}`;
            onData(line);
            sampleIndex++;
        }, 10); // 10ms per sample
    };

    return { isSupported, isConnected, connect, disconnect, startReading, stopReading, mockSimulate };
};
