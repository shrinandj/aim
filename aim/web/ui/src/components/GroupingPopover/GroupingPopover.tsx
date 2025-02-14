import React from 'react';

import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Checkbox,
  TextField,
} from '@material-ui/core';
import {
  CheckBox as CheckBoxIcon,
  CheckBoxOutlineBlank,
} from '@material-ui/icons';
import Autocomplete from '@material-ui/lab/Autocomplete';

import { Badge, Icon, Text, ToggleButton } from 'components/kit';
import ErrorBoundary from 'components/ErrorBoundary/ErrorBoundary';

import { IGroupingPopoverProps } from 'types/components/GroupingPopover/GroupingPopover';
import {
  GroupNameType,
  IGroupingSelectOption,
} from 'types/services/models/metrics/metricsAppModel';

import './GroupingPopover.scss';

function GroupingPopover({
  groupName,
  advancedComponent,
  groupingData,
  groupingSelectOptions,
  onSelect,
  onGroupingModeChange,
}: IGroupingPopoverProps): React.FunctionComponentElement<React.ReactNode> {
  const [inputValue, setInputValue] = React.useState('');

  function onChange(e: any, values: IGroupingSelectOption[]): void {
    if (e?.code !== 'Backspace') {
      handleSelect(values);
      setInputValue('');
    } else {
      if (inputValue.length === 0) {
        handleSelect(values);
      }
    }
  }

  function handleSelect(values: IGroupingSelectOption[]) {
    onSelect({
      groupName,
      list: values.map((item: IGroupingSelectOption) =>
        typeof item === 'string' ? item : item.value,
      ),
    });
  }

  const values: IGroupingSelectOption[] = React.useMemo(() => {
    let data: { value: string; group: string; label: string }[] = [];
    groupingSelectOptions.forEach((option) => {
      if (groupingData?.[groupName].indexOf(option.value) !== -1) {
        data.push(option);
      }
    });

    // Sort selected values by the order of their application
    return groupingData
      ? data.sort(
          (a, b) =>
            groupingData[groupName].indexOf(a.value) -
            groupingData[groupName].indexOf(b.value),
        )
      : data;
  }, [groupName, groupingData, groupingSelectOptions]);

  function handleGroupingMode(val: string | number, id: any) {
    onGroupingModeChange({
      groupName,
      value: val === 'Reverse',
      options: groupingData?.reverseMode[groupName as GroupNameType]
        ? groupingSelectOptions
        : null,
    });
  }

  const options = React.useMemo(() => {
    if (inputValue.trim() !== '') {
      const filtered = groupingSelectOptions.filter((item) => {
        return item.label.indexOf(inputValue) !== -1;
      });

      return filtered
        .slice()
        .sort(
          (a, b) => a.label.indexOf(inputValue) - b.label.indexOf(inputValue),
        );
    }
    return groupingSelectOptions;
  }, [groupingSelectOptions, inputValue]);

  return (
    <ErrorBoundary>
      <div className='GroupingPopover'>
        <div className='GroupingPopover__container'>
          <div className='GroupingPopover__container__select'>
            <Text
              size={12}
              tint={50}
              component='h3'
              className='GroupingPopover__subtitle'
            >
              Select Fields for grouping by {groupName}
            </Text>
            <Autocomplete
              size='small'
              multiple
              disableCloseOnSelect
              options={options}
              value={values}
              onChange={onChange}
              groupBy={(option) => option.group}
              getOptionLabel={(option) => option.label}
              getOptionSelected={(option, value) =>
                option.value === value.value
              }
              renderInput={(params: any) => (
                <TextField
                  {...params}
                  inputProps={{
                    ...params.inputProps,
                    value: inputValue,
                    onChange: (e: any) => {
                      setInputValue(e.target?.value);
                    },
                  }}
                  variant='outlined'
                  placeholder='Select Params'
                />
              )}
              renderTags={(value, getTagProps) => (
                <div style={{ maxHeight: 110, overflow: 'auto' }}>
                  {value.map((selected, i) => (
                    <Badge
                      key={i}
                      {...getTagProps({ index: i })}
                      label={selected.label}
                      selectBadge={true}
                    />
                  ))}
                </div>
              )}
              renderOption={(option, { selected }) => (
                <React.Fragment>
                  <Checkbox
                    color='primary'
                    size='small'
                    icon={<CheckBoxOutlineBlank />}
                    checkedIcon={<CheckBoxIcon />}
                    style={{ marginRight: 4 }}
                    checked={selected}
                  />
                  {option.label}
                </React.Fragment>
              )}
            />
          </div>
          <div className='GroupingPopover__toggleMode__div'>
            <Text
              size={12}
              tint={50}
              component='h3'
              className='GroupingPopover__subtitle'
            >
              select grouping mode
            </Text>
            <ToggleButton
              title='Select Mode'
              id='yAxis'
              value={
                groupingData?.reverseMode[groupName as GroupNameType]
                  ? 'Reverse'
                  : 'Group'
              }
              leftValue='Group'
              rightValue='Reverse'
              leftLabel='Group'
              rightLabel='Reverse'
              onChange={handleGroupingMode}
            />
          </div>
          {advancedComponent && (
            <ErrorBoundary>
              <div className='GroupingPopover__advanced__component'>
                <Accordion className='GroupingPopover__accordion__container'>
                  <AccordionSummary
                    expandIcon={
                      <Icon
                        fontSize='0.875rem'
                        name='arrow-bidirectional-close'
                      />
                    }
                    id='panel1c-header'
                  >
                    <Text
                      size={12}
                      tint={50}
                      component='h3'
                      weight={400}
                      className='GroupingPopover__subtitle'
                    >
                      Advanced options
                    </Text>
                  </AccordionSummary>
                  <AccordionDetails style={{ padding: 0 }}>
                    {advancedComponent}
                  </AccordionDetails>
                </Accordion>
              </div>
            </ErrorBoundary>
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
}

export default GroupingPopover;
