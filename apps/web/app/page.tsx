import CampaignStudio from './studio';
export const dynamic = 'force-dynamic';
export default function Home() {
  return <CampaignStudio mode={process.env.APP_MODE || 'demo'} />;
}
