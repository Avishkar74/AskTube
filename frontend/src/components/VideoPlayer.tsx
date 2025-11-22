import React, { useRef, useEffect } from 'react';
import ReactPlayer from 'react-player';

interface VideoPlayerProps {
    url: string;
    onProgress: (state: any) => void;
    onReady: () => void;
    seekTo?: number | null;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ url, onProgress, onReady, seekTo }) => {
    const playerRef = useRef<any>(null);

    useEffect(() => {
        if (seekTo !== null && seekTo !== undefined && playerRef.current) {
            playerRef.current.seekTo(seekTo, 'seconds');
        }
    }, [seekTo]);

    return (
        <div className="relative pt-[56.25%] w-full bg-black rounded-lg overflow-hidden shadow-lg">
            <ReactPlayer
                ref={playerRef}
                url={url}
                className="absolute top-0 left-0"
                width="100%"
                height="100%"
                controls
                onProgress={onProgress}
                onReady={onReady}
                config={{
                    youtube: {
                        playerVars: { showinfo: 1 }
                    }
                }}
            />
        </div>
    );
};

export default VideoPlayer;
