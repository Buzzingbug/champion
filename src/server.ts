import express from 'express';
import { createBullBoard } from '@bull-board/api';
import { BullMQAdapter } from '@bull-board/api/bullMQAdapter';
import { ExpressAdapter } from '@bull-board/express';
import { gameQueue, systemQueue } from './jobs';

export function startServer() {
  const app = express();
  const serverAdapter = new ExpressAdapter();
  serverAdapter.setBasePath('/admin/queues');

  createBullBoard({
    queues: [new BullMQAdapter(gameQueue as any), new BullMQAdapter(systemQueue as any)],
    serverAdapter: serverAdapter,
  });

  app.use('/admin/queues', serverAdapter.getRouter());
  
  app.get('/', (req, res) => {
    res.send('Champion Bot is online and running.');
  });

  const port = process.env.PORT || 3000;
  app.listen(port, () => {
    console.log(`[Express] Dashboard available at http://localhost:${port}/admin/queues`);
  });
}
