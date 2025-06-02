'use client';

import React from "react";

const bgImages = [
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/sone00682/sone00682ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/nima00045/nima00045ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/sone00687/sone00687ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/dsvr00052/dsvr00052ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/nima00049/nima00049ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/royd00213/royd00213ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/ngod00253/ngod00253ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/jums00066/jums00066ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/savr00631/savr00631ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/mkmp00601/mkmp00601ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/xvsr00810/xvsr00810ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/lulu00328/lulu00328ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/usba00083/usba00083ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/cspl00013/cspl00013ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/savr00362/savr00362ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/pfes00058/pfes00058ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/lulu00243/lulu00243ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/bnst00078/bnst00078ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/1namh00007/1namh00007ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/gdrd00006/gdrd00006ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/ofje00484/ofje00484ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/hnvr00139/hnvr00139ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/mudr00282/mudr00282ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/dass00572/dass00572ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/cawd00817/cawd00817ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/h_237nacr00850/h_237nacr00850ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/mdvr00348/mdvr00348ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/mdbk00338/mdbk00338ps.jpg?w=147&h=200&f=webp&t=margin",
  "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/midv00946/midv00946ps.jpg?w=147&h=200&f=webp&t=margin",
] as const;

export function BackgroundImages() {
  return (
    <div className="fixed z-0 grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8 w-full h-full pointer-events-none top-0 left-0 right-0 bottom-0 mx-auto">
      {bgImages.map((url: string, idx: number) => (
        <div key={idx} className="w-full h-full aspect-[1/1.361] relative">
          <img
            src={url}
            alt="bg"
            className="object-cover w-full h-full opacity-60 select-none blur-sm"
            draggable={false}
            loading="lazy"
            fetchPriority="low"
          />
        </div>
      ))}
      {/* オーバーレイ */}
      <div className="absolute inset-0 bg-black opacity-60" />
    </div>
  );
} 