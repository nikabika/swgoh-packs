import { NextResponse } from 'next/server';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const allyCode = searchParams.get('code');

  if (!allyCode) {
    return NextResponse.json({ error: 'Missing ally code' }, { status: 400 });
  }

  const targetUrl = `https://swgoh.gg/api/player/${allyCode}/`;

  try {
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://swgoh.gg/'
      },
      // Отключаем жесткое кэширование Vercel, чтобы данные всегда были свежими
      cache: 'no-store' 
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: `Swgoh returning status ${response.status}` }, 
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
