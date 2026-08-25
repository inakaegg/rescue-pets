// 画像そのものは別リポジトリ pets-image が生成する。ここでは配信する資産としての体裁だけを検査する。
import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { readdir, readFile } from 'node:fs/promises'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const repositoryRoot = fileURLToPath(new URL('..', import.meta.url))
const photoDirectory = path.join(repositoryRoot, 'public', 'pets')
// 素材リポジトリ pets-image が生成した現物と同じであることを固定する。寸法と容量だけの検査では、
// 同じ体裁で再エンコードした別物へ差し替えられても気づけない。
const digestFile = path.join(repositoryRoot, 'scripts', 'pet-photos.sha256')
const expectedCount = 50
const maxBytes = 250 * 1024

// 途中で切れたファイルでも先頭のヘッダーだけは読めてしまう。RIFF の申告長と各チャンクの収まりも確かめて、
// 壊れた画像が「1024×1024 の WebP」として通り抜けるのを防ぐ。
function readWebpDimensions(buffer) {
  assert.equal(buffer.subarray(0, 4).toString(), 'RIFF')
  assert.equal(buffer.subarray(8, 12).toString(), 'WEBP')
  assert.equal(buffer.readUInt32LE(4) + 8, buffer.length, 'RIFF の申告サイズがファイル長と違う')
  let offset = 12
  while (offset + 8 <= buffer.length) {
    const type = buffer.subarray(offset, offset + 4).toString()
    const length = buffer.readUInt32LE(offset + 4)
    assert.ok(offset + 8 + length <= buffer.length, `${type} チャンクが途中で切れている`)
    const data = buffer.subarray(offset + 8, offset + 8 + length)
    if (type === 'VP8 ') {
      assert.deepEqual([...data.subarray(3, 6)], [0x9d, 0x01, 0x2a])
      return { width: data.readUInt16LE(6) & 0x3fff, height: data.readUInt16LE(8) & 0x3fff }
    }
    if (type === 'VP8L') {
      assert.equal(data[0], 0x2f)
      const bits = data.readUInt32LE(1)
      return { width: (bits & 0x3fff) + 1, height: ((bits >> 14) & 0x3fff) + 1 }
    }
    if (type === 'VP8X') {
      return {
        width: data.readUIntLE(4, 3) + 1,
        height: data.readUIntLE(7, 3) + 1,
      }
    }
    offset += 8 + length + (length % 2)
  }
  throw new Error('WebP image chunk not found')
}

// .DS_Store のような無視対象が混ざっても件数がずれないよう、拡張子で絞る。
async function photoFiles() {
  return (await readdir(photoDirectory)).filter((file) => file.endsWith('.webp')).sort()
}

test('public/pets holds the fifty sample photos', async () => {
  const files = await photoFiles()
  assert.equal(files.length, expectedCount)
  for (const file of files) assert.match(file, /^sample-[a-z]+\.webp$/)
})

test('every photo is a complete 1024px WebP, bounded in size, and unique', async () => {
  const hashes = new Set()
  for (const file of await photoFiles()) {
    const photo = await readFile(path.join(photoDirectory, file))
    assert.ok(photo.length <= maxBytes, `${file} is ${photo.length} bytes`)
    assert.deepEqual(readWebpDimensions(photo), { width: 1024, height: 1024 })
    hashes.add(createHash('sha256').update(photo).digest('hex'))
  }
  assert.equal(hashes.size, expectedCount)
})

test('every photo matches the digest recorded for the source material', async () => {
  const expected = new Map(
    (await readFile(digestFile, 'utf8'))
      .split('\n')
      .filter(Boolean)
      .map((line) => {
        const [hash, file] = line.split(/\s+/)
        return [file, hash]
      }),
  )
  const files = await photoFiles()
  assert.deepEqual(files, [...expected.keys()].sort())
  for (const file of files) {
    const photo = await readFile(path.join(photoDirectory, file))
    assert.equal(createHash('sha256').update(photo).digest('hex'), expected.get(file), file)
  }
})

test('a truncated photo is rejected instead of read as 1024px', async () => {
  const [first] = await photoFiles()
  const photo = await readFile(path.join(photoDirectory, first))
  assert.throws(() => readWebpDimensions(photo.subarray(0, 30)))
  assert.throws(() => readWebpDimensions(photo.subarray(0, photo.length - 1)))
})
