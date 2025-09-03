import React from 'react';
import { PanelProps } from '@grafana/data';
import { SimpleOptions } from '../../types';

interface Props extends PanelProps<SimpleOptions> {}

export const Panel: React.FC<Props> = ({ options, data, width, height }) => {
  return (
    <div style={{ width, height, overflow: 'auto' }}>
      <h2>Hello from Tapo Camera Stream Panel</h2>
      <p>This is a placeholder for the Tapo camera stream.</p>
    </div>
  );
};
