import { PanelPlugin } from '@grafana/data';
import { SimpleOptions } from './types';
import { TapoCameraStreamPanel } from './components/TapoCameraStreamPanel';
import { PanelOptions } from './components/PanelOptions';

export const plugin = new PanelPlugin<SimpleOptions>(TapoCameraStreamPanel).setPanelOptions((builder) => {
  return builder
    .addTextInput({
      path: 'streamUrl',
      name: 'Stream URL',
      description: 'URL for the camera stream (RTSP, RTMP, HLS, etc.)',
      settings: {
        placeholder: 'rtsp://camera-address/stream',
      },
    })
    .addSelect({
      path: 'streamType',
      name: 'Stream Type',
      description: 'Type of video stream',
      defaultValue: 'hls',
      settings: {
        options: [
          { value: 'hls', label: 'HLS' },
          { value: 'rtsp', label: 'RTSP' },
          { value: 'rtmp', label: 'RTMP' },
          { value: 'webrtc', label: 'WebRTC' },
          { value: 'mjpeg', label: 'MJPEG' },
        ],
      },
    })
    .addBooleanSwitch({
      path: 'showControls',
      name: 'Show Controls',
      description: 'Show playback controls',
      defaultValue: true,
    })
    .addBooleanSwitch({
      path: 'autoPlay',
      name: 'Auto Play',
      description: 'Automatically start playing the stream',
      defaultValue: true,
    })
    .addBooleanSwitch({
      path: 'muted',
      name: 'Muted',
      description: 'Mute audio by default',
      defaultValue: true,
    })
    .addNumberInput({
      path: 'maxWidth',
      name: 'Max Width',
      description: 'Maximum width of the video player (0 for auto)',
      defaultValue: 0,
    });
});
