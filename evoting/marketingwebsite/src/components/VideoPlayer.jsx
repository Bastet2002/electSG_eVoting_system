import React from 'react';
import ReactPlayer from 'react-player';
import Video from '../assets/video.mp4';


const VideoPlayer = () => {
  return (
    <div>
        <ReactPlayer controls={true} url={Video} height="1000%" width="100%"/>
    </div>
  )
}

export default VideoPlayer
