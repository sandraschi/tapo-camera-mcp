import { PanelPlugin } from '@grafana/data';
import { TapoCameraStreamPanel } from './components/TapoCameraStreamPanel';
import { SimpleOptions } from '../types';

export const plugin = new PanelPlugin<SimpleOptions>(TapoCameraStreamPanel)
  .setPanelOptions((builder) => {
    return builder
      .addTextInput({
        path: 'streamUrl',
        name: 'Stream URL',
        description: 'URL of the camera stream (RTSP, HLS, RTMP, WebRTC, or MJPEG)',
        defaultValue: '',
      })
      .addSelect({
        path: 'streamType',
        name: 'Stream Type',
        description: 'Type of the video stream',
        settings: {
          options: [
            { value: 'hls', label: 'HLS' },
            { value: 'rtsp', label: 'RTSP' },
            { value: 'rtmp', label: 'RTMP' },
            { value: 'webrtc', label: 'WebRTC' },
            { value: 'mjpeg', label: 'MJPEG' },
          ],
        },
        defaultValue: 'hls',
      })
      .addBooleanSwitch({
        path: 'useAuth',
        name: 'Use Authentication',
        description: 'Enable if the stream requires authentication',
        defaultValue: false,
      })
      .addTextInput({
        path: 'username',
        name: 'Username',
        description: 'Username for authentication',
        defaultValue: '',
        showIf: (config) => config.useAuth,
      })
      .addTextInput({
        path: 'password',
        name: 'Password',
        description: 'Password for authentication',
        defaultValue: '',
        showIf: (config) => config.useAuth,
      })
      .addBooleanSwitch({
        path: 'showControls',
        name: 'Show Controls',
        description: 'Show video player controls',
        defaultValue: true,
      })
      .addBooleanSwitch({
        path: 'autoPlay',
        name: 'Auto Play',
        description: 'Start playing the stream automatically',
        defaultValue: true,
      })
      .addBooleanSwitch({
        path: 'muted',
        name: 'Muted',
        description: 'Mute audio by default',
        defaultValue: true,
      })
      .addBooleanSwitch({
        path: 'showPtzControls',
        name: 'Show PTZ Controls',
        description: 'Show Pan-Tilt-Zoom controls',
        defaultValue: true,
      });
  });
