import React, { useRef, useEffect, useState } from 'react';
import YouTube, { type YouTubeProps } from 'react-youtube';

interface VideoPlayerProps {
    videoId: string;
    onProgress: (state: { playedSeconds: number }) => void;
    onReady: () => void;
    seekTo?: number | null;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ videoId, onProgress, onReady, seekTo }) => {
    const playerRef = useRef<any>(null);
    const [hasError, setHasError] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const progressInterval = useRef<ReturnType<typeof setInterval> | null>(null);

    console.log('[VideoPlayer] Render. VideoID:', videoId, 'isLoading:', isLoading);

    // Handle seeking
    useEffect(() => {
        if (seekTo !== null && seekTo !== undefined && playerRef.current) {
            console.log('[VideoPlayer] Seeking to:', seekTo);
            playerRef.current.seekTo(seekTo, true);
        }
    }, [seekTo]);

    // Cleanup interval on unmount
    useEffect(() => {
        return () => {
            if (progressInterval.current) {
                clearInterval(progressInterval.current);
            }
        };
    }, []);

    const onPlayerReady: YouTubeProps['onReady'] = (event) => {
        console.log('[VideoPlayer] onReady');
        playerRef.current = event.target;
        setIsLoading(false);
        onReady();
    };

    const onPlayerStateChange: YouTubeProps['onStateChange'] = (event) => {
        // 1 = playing, 2 = paused
        if (event.data === 1) {
            // Start progress tracking
            if (progressInterval.current) clearInterval(progressInterval.current);
            progressInterval.current = setInterval(() => {
                const currentTime = event.target.getCurrentTime();
                onProgress({ playedSeconds: currentTime });
            }, 1000);
        } else {
            // Stop progress tracking
            if (progressInterval.current) clearInterval(progressInterval.current);
        }
    };

    const onPlayerError: YouTubeProps['onError'] = (event) => {
        console.error("[VideoPlayer] Error:", event.data);
        setHasError(true);
        setIsLoading(false);
    };

    const opts: YouTubeProps['opts'] = {
        height: '100%',
        width: '100%',
        playerVars: {
            autoplay: 1,
            controls: 1,
            modestbranding: 1,
            rel: 0,
        },
    };

    if (!videoId) {
        return (
            <div className="relative pt-[56.25%] w-full bg-zinc-900 rounded-lg overflow-hidden shadow-lg flex items-center justify-center">
                <div className="absolute inset-0 flex items-center justify-center text-zinc-500">
                    <p>No video ID provided</p>
                </div>
            </div>
        );
    }

    return (
        <div className="relative pt-[56.25%] w-full bg-black rounded-lg overflow-hidden shadow-lg group">
            {isLoading && (
                <div className="absolute inset-0 flex items-center justify-center z-10 bg-zinc-900/50">
                    <div className="w-10 h-10 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
                </div>
            )}

            {hasError ? (
                <div className="absolute inset-0 flex items-center justify-center bg-zinc-900 text-zinc-400">
                    <p>Failed to load video</p>
                </div>
            ) : (
                <div className="absolute inset-0">
                    <YouTube
                        videoId={videoId}
                        opts={opts}
                        onReady={onPlayerReady}
                        onStateChange={onPlayerStateChange}
                        onError={onPlayerError}
                        className="w-full h-full"
                        iframeClassName="w-full h-full"
                    />
                </div>
            )}
        </div>
    );
};

export default VideoPlayer;
