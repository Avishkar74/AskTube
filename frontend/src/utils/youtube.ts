export const normalizeYoutubeUrl = (url: string): string => {
    if (!url) return '';

    // Handle already correct format
    if (url.includes('youtube.com/watch?v=')) {
        return url;
    }

    // Extract ID
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    const videoId = (match && match[2].length === 11) ? match[2] : null;

    if (videoId) {
        return `https://www.youtube.com/watch?v=${videoId}`;
    }

    return url;
};
