import React from 'react';
import { PanelOptionsEditorProps } from '@grafana/data';
import { SimpleOptions } from '../../types';

type Props = PanelOptionsEditorProps<SimpleOptions>;

export const PanelOptions: React.FC<Props> = ({ value, onChange }) => {
  // The actual options are defined in module.ts using the builder pattern
  // This component is just a placeholder
  return null;
};
