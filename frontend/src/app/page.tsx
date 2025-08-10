'use client';

import { Header } from '@/components/layout/Header';
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Input,
  Badge,
} from '@/components/ui';
import { VoiceRecorder } from '@/components/features';
import { MicrophoneIcon, PaperAirplaneIcon } from '@heroicons/react/24/outline';

export default function Home() {
  return (
    <div className='min-h-screen'>
      <Header isConnected={true} connectionStatus='connected' />

      <main className='mx-auto max-w-4xl p-6'>
        {/* Demo Section */}
        <div className='mb-8'>
          <h2 className='mb-4 text-2xl font-bold text-gray-900'>
            UI Components Demo
          </h2>
          <p className='text-gray-600'>
            Testing our design system components before building the main app.
          </p>
        </div>

        {/* Components Grid */}
        <div className='grid grid-cols-1 gap-6 lg:grid-cols-2'>
          {/* Buttons Card */}
          <Card>
            <CardHeader>
              <CardTitle>Buttons</CardTitle>
            </CardHeader>
            <CardContent>
              <div className='space-y-4'>
                <div className='flex flex-wrap gap-2'>
                  <Button variant='primary'>Primary</Button>
                  <Button variant='secondary'>Secondary</Button>
                  <Button variant='outline'>Outline</Button>
                  <Button variant='ghost'>Ghost</Button>
                  <Button variant='danger'>Danger</Button>
                </div>
                <div className='flex flex-wrap gap-2'>
                  <Button size='sm'>Small</Button>
                  <Button size='md'>Medium</Button>
                  <Button size='lg'>Large</Button>
                </div>
                <div className='flex flex-wrap gap-2'>
                  <Button leftIcon={<MicrophoneIcon className='h-4 w-4' />}>
                    With Icon
                  </Button>
                  <Button isLoading>Loading</Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Badges Card */}
          <Card>
            <CardHeader>
              <CardTitle>Badges</CardTitle>
            </CardHeader>
            <CardContent>
              <div className='space-y-4'>
                <div className='flex flex-wrap gap-2'>
                  <Badge>Default</Badge>
                  <Badge variant='primary'>Primary</Badge>
                  <Badge variant='success'>Success</Badge>
                  <Badge variant='warning'>Warning</Badge>
                  <Badge variant='error'>Error</Badge>
                </div>
                <div className='flex flex-wrap gap-2'>
                  <Badge dot variant='success'>
                    Connected
                  </Badge>
                  <Badge dot variant='warning'>
                    Connecting
                  </Badge>
                  <Badge dot variant='error'>
                    Error
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Inputs Card */}
          <Card>
            <CardHeader>
              <CardTitle>Inputs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className='space-y-4'>
                <Input label='Default Input' placeholder='Type something...' />
                <Input
                  label='With Icon'
                  placeholder='Send a message...'
                  rightIcon={<PaperAirplaneIcon className='h-4 w-4' />}
                />
                <Input
                  label='With Error'
                  error='This field is required'
                  placeholder='Invalid input'
                />
                <Input
                  label='With Helper'
                  helper='This is a helper text'
                  placeholder='With helper text'
                />
              </div>
            </CardContent>
          </Card>

          {/* Cards Demo */}
          <Card>
            <CardHeader>
              <CardTitle>Card Variants</CardTitle>
            </CardHeader>
            <CardContent>
              <div className='space-y-4'>
                <Card variant='bordered' padding='sm'>
                  <p className='text-sm'>Bordered Card</p>
                </Card>
                <Card variant='shadow' padding='sm' hover>
                  <p className='text-sm'>Shadow Card with Hover</p>
                </Card>
                <Card variant='elevated' padding='sm'>
                  <p className='text-sm'>Elevated Card</p>
                </Card>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Voice Interface */}
        <Card className='mt-8'>
          <CardHeader>
          <CardTitle>Voice Recording Demo</CardTitle>
          </CardHeader>
          <CardContent>
            <VoiceRecorder
              onRecordingComplete={audioBlob => {
                console.log('Recording completed:', audioBlob);
                // Here we'll later integrate with the backend
              }}
              onError={error => {
                console.error('Recording error:', error);
              }}
              maxDuration={60} // 1 minute for demo
            />
          </CardContent>
        </Card>

        {/* Navigation to Chat */}
        <Card className='mt-8'>
          <CardHeader>
            <CardTitle>Ready to Chat?</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='text-center py-4'>
              <p className='text-gray-600 mb-4'>
                Try the full voice-enabled chat experience with AI integration.
              </p>
              <Button
                variant='primary'
                size='lg'
                onClick={() => window.location.href = '/chat'}
                leftIcon={<MicrophoneIcon className='h-6 w-6' />}
              >
                Open Voice Chat
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
