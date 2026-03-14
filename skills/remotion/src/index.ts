import {registerRoot} from 'remotion';
import {TypeA} from './compositions/TypeA';
import TypeB from './compositions/TypeB';

registerRoot(() => {
  return (
    <>
      <TypeA {...TypeA.typeADefaultProps} />
      <TypeB {...TypeB.typeBDefaultProps} />
    </>
  );
});
