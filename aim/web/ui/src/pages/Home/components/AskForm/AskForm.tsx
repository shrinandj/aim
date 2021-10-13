import React from 'react';
import { TextField } from '@material-ui/core';

import Button from 'components/Button/Button';
import { IAskFormProps } from 'types/pages/home/components/AskForm/AskForm';

import avatarImg from 'assets/gevImg.jpeg';
import './AskForm.scss';

function AskForm({
  onSendEmail,
}: IAskFormProps): React.FunctionComponentElement<React.ReactNode> {
  const [email, setEmail] = React.useState<string>('');

  async function handleSubmit() {
    const data = await onSendEmail({ email });
    if (data.ok) {
      setEmail('');
    }
  }

  function onChange(e: React.ChangeEvent<any>): void {
    setEmail(e.target.value);
  }

  return (
    <div className='AskForm'>
      <div className='AskForm__avatar'>
        <img src={avatarImg} alt='Avatar' />
      </div>
      <h2 className='AskForm__title'>👋 Hey, I’m Gev, co-author of Aim</h2>
      <p className='AskForm__p'>
        We’re working hard to create an amazing experiment tracker and need your
        feedback for the Aim 3.0.0 beta version. If you’d like to contribute to
        improving it and share what you like/dislike about Aim, please leave
        your email and I’ll reach out asap.
      </p>
      <TextField
        className='TextField__OutLined__Large'
        placeholder='Write your email'
        variant='outlined'
        onChange={onChange}
        value={email}
      />
      <Button
        onClick={handleSubmit}
        variant='contained'
        className='AskForm__submit'
      >
        Submit
      </Button>
    </div>
  );
}

export default AskForm;