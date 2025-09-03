export interface PanelOptions {
  streamUrl: string;
  streamType: 'hls' | 'rtsp' | 'rtmp' | 'webrtc' | 'mjpeg';
  useAuth: boolean;
  username: string;
  password: string;
  showControls: boolean;
  autoPlay: boolean;
  muted: boolean;
  showPtzControls: boolean;
}

export interface PTZPreset {
  id: number;
  name: string;
  position: {
    pan: number;
    tilt: number;
    zoom: number;
  };
}
