import { RequestStatusEnum } from 'config/enums/requestStatusEnum';

import { IModel, State } from 'types/services/models/model';

import onNotificationAdd from './onNotificationAdd';
import resetModelOnError from './resetModelOnError';

export default function exceptionHandler<M extends State>({
  detail,
  model,
}: {
  detail: any;
  model: IModel<M>;
}) {
  let message = '';
  if (detail.name === 'SyntaxError') {
    message = `Query syntax error at line (${detail.line}, ${detail.offset})`;
  } else {
    message = detail.message || 'Something went wrong';
  }
  model.setState({ requestStatus: RequestStatusEnum.BadRequest });
  onNotificationAdd({
    notification: {
      id: Date.now(),
      severity: 'error',
      messages: [message],
    },
    model,
  });

  // reset model
  resetModelOnError({ detail, model });
}
